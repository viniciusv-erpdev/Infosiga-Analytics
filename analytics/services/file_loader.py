import io
import os

from django.http import request
import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect

from analytics.forms import UploadFileForm
from analytics.persistence import dataset
from analytics.services.filters import apply_filters
from analytics.services.preprocessing.address_normalizer import normalize_address
from analytics.services.preprocessing.pipeline import run_preprocessing
from analytics.services.dataset_service import DatasetService

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


def get_file_info(arquivo):
    """Retorna informações básicas do arquivo enviado."""
    if arquivo is None:
        return None

    nome = arquivo.name
    extensao = os.path.splitext(nome)[1].lower()
    tamanho_kb = round(arquivo.size / 1024, 2)

    return {
        "nome": nome,
        "extensao": extensao,
        "tamanho_kb": tamanho_kb,
    }


def load_dataframe(arquivo):
    """Lê o arquivo enviado com pandas e retorna um DataFrame."""

    extensao = arquivo.name.rsplit(".", 1)[-1].lower()

    if extensao == "xlsx":
        arquivo.seek(0)
        return pd.read_excel(arquivo)

    codificacoes = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1",
    ]

    for encoding in codificacoes:
        try:
            print(f"Tentando {encoding}")
            arquivo.seek(0)
            text_stream = io.TextIOWrapper(
                arquivo.file,
                encoding=encoding,
            )
            try:
                return pd.read_csv(
                    text_stream,
                    sep=";",
                    engine="python",
                )
            finally:
                text_stream.detach()
        except Exception as e:
            print(f"Falhou com {encoding}: {e}")

    raise ValueError("Não foi possível abrir o arquivo CSV.")


def build_audit_rows(dataframe):
    """Prepara os dados exibidos na auditoria de regularização sem alterar o fluxo do pipeline."""
    if dataframe is None:
        return {"columns": [], "rows": []}

    audit_dataframe = dataframe.copy()

    if "logradouro_normalizado" not in audit_dataframe.columns:
        if "logradouro" in audit_dataframe.columns:
            audit_dataframe["logradouro_normalizado"] = audit_dataframe["logradouro"].apply(normalize_address)
        else:
            audit_dataframe["logradouro_normalizado"] = ""

    if "logradouro_limpo" not in audit_dataframe.columns:
        if "logradouro_normalizado" in audit_dataframe.columns:
            from analytics.services.preprocessing.address_semantic_cleaner import clean_semantic_address

            audit_dataframe["logradouro_limpo"] = audit_dataframe["logradouro_normalizado"].apply(clean_semantic_address)
        else:
            audit_dataframe["logradouro_limpo"] = ""

    if "logradouro_canonico" not in audit_dataframe.columns:
        audit_dataframe["logradouro_canonico"] = audit_dataframe["logradouro_limpo"].fillna("")

    if "similaridade" not in audit_dataframe.columns:
        audit_dataframe["similaridade"] = None

    if "frequencia_grupo" not in audit_dataframe.columns:
        audit_dataframe["frequencia_grupo"] = 0

    rows = []
    for _, row in audit_dataframe.head(20).iterrows():
        similarity_value = row.get("similaridade")
        if pd.isna(similarity_value) or similarity_value is None:
            similarity_display = "-"
        elif isinstance(similarity_value, (int, float)):
            similarity_display = f"{float(similarity_value):.0f}%"
        else:
            similarity_display = str(similarity_value)

        frequency_value = row.get("frequencia_grupo")
        if pd.isna(frequency_value) or frequency_value is None:
            frequency_display = 0
        else:
            frequency_display = int(frequency_value)

        rows.append(
            [
                row.get("logradouro", ""),
                row.get("logradouro_normalizado", ""),
                row.get("logradouro_limpo", ""),
                row.get("logradouro_canonico", ""),
                similarity_display,
                frequency_display,
            ]
        )

    return {
        "columns": [
            "Logradouro original",
            "Logradouro normalizado",
            "Logradouro limpo",
            "Logradouro canônico",
            "Similaridade (%)",
            "Frequência do grupo",
        ],
        "rows": rows,
    }


def build_preview_data(dataframe):
    """Cria a estrutura de pré-visualização a partir do DataFrame processado."""
    if dataframe is None:
        return {
            "columns": [],
            "rows": [],
            "regularization_columns": [],
            "regularization_rows": [],
            "audit_columns": [],
            "audit_rows": [],
        }

    columns_to_show = [col for col in ["logradouro", "logradouro_normalizado"] if col in dataframe.columns]
    regularization_columns = [
        col
        for col in ["logradouro", "logradouro_normalizado", "logradouro_canonico", "similaridade", "frequencia_grupo"]
        if col in dataframe.columns
    ]
    audit_data = build_audit_rows(dataframe)

    return {
        "columns": columns_to_show,
        "rows": dataframe[columns_to_show].head(20).values.tolist(),
        "regularization_columns": regularization_columns,
        "regularization_rows": dataframe[regularization_columns].head(20).values.tolist(),
        "audit_columns": audit_data["columns"],
        "audit_rows": audit_data["rows"],
    }


def process_upload(request):
    """Processa o upload do arquivo e retorna o formulário para a view."""
    if request.method != "POST":
        return UploadFileForm(), None

    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid():
        return form, None

    print("[DEBUG] formulário válido")
    print("[DEBUG] usuário:", request.user)
    print("[DEBUG] autenticado:", request.user.is_authenticated)

    arquivo = form.cleaned_data["arquivo"]
    file_info = get_file_info(arquivo)

    if not file_info:
        messages.error(request, "Nenhum arquivo foi enviado.")
        return form, redirect("home")

    extensao = file_info["extensao"]
    if extensao not in ALLOWED_EXTENSIONS:
        messages.error(request, "Extensão de arquivo inválida. Apenas .csv e .xlsx são permitidos.")
        return form, redirect("home")

    try:
        print("[DEBUG] antes de load_dataframe")
        dataframe = load_dataframe(arquivo)
        print("[DEBUG] depois de load_dataframe")
    except ValueError as exc:
        messages.error(request, str(exc))
        return form, redirect("home")

    tipo_via = request.POST.get("tipo_via")
    tipo_sinistro = request.POST.get("tipo_sinistro")
    print(f"[DEBUG] tipo_via recebido: {tipo_via}")
    print(f"[DEBUG] tipo_sinistro recebido: {tipo_sinistro}")
    print(f"[DEBUG] linhas antes dos filtros: {len(dataframe)}")

    dataframe_filtrado = apply_filters(dataframe, tipo_via=tipo_via, tipo_sinistro=tipo_sinistro)
    print(f"[DEBUG] linhas depois dos filtros: {len(dataframe_filtrado)}")

    if not request.user.is_authenticated:
        messages.error(
            request,
            "É necessário estar autenticado para realizar um upload."
        )
        return form, redirect("home")

    print("[DEBUG] antes de criar Dataset")

    dataset = DatasetService.create_from_upload(
        usuario=request.user,
        arquivo=arquivo,
        quantidade_registros=len(dataframe),
    )

    print(f"[DEBUG] Dataset criado: {dataset.id}")
    print(f"[DEBUG] arquivo salvo: {dataset.arquivo.name}")

    try:
        dataframe_processado = run_preprocessing(dataframe_filtrado)

        dataset = DatasetService.save_processed_dataframe(
            dataset=dataset,
            dataframe=dataframe_processado,
        )
    except Exception:
        DatasetService.delete(dataset)
        messages.error(
            request,
            "Não foi possível processar o arquivo enviado.",
        )
        return form, redirect("home")

    print("[DEBUG] preprocessing concluído")

    request.session["last_dataset_id"] = dataset.id
    request.session["uploaded_file_info"] = {
        "nome": file_info["nome"],
        "tamanho_kb": file_info["tamanho_kb"],
        "extensao": extensao,
    }
    request.session.modified = True

    messages.success(
        request,
        f"Arquivo recebido: {file_info['nome']} | Extensão: {extensao} | Tamanho: {file_info['tamanho_kb']} KB",
    )
    messages.info(request, f"Linhas restantes: {len(dataframe_filtrado)}")
    messages.info(request, f"Colunas: {len(dataframe_filtrado.columns)}")
    messages.info(request, f"Registros encontrados: {len(dataframe_filtrado)}")
    return form, redirect("home")
