import os

import pandas as pd
from django.contrib import messages
from django.shortcuts import redirect

from analytics.forms import UploadFileForm
from analytics.services.filters import apply_filters
from analytics.services.preprocessing.pipeline import run_preprocessing


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
        return pd.read_excel(arquivo)

    caminho_arquivo = arquivo.temporary_file_path()

    codificacoes = [
        "utf-8",
        "utf-8-sig",
        "cp1252",
        "latin1",
    ]

    for encoding in codificacoes:
        try:
            print(f"Tentando {encoding}")
            return pd.read_csv(
                caminho_arquivo,
                sep=";",
                encoding=encoding,
                engine="python",
            )
        except Exception as e:
            print(f"Falhou com {encoding}: {e}")

    raise ValueError("Não foi possível abrir o arquivo CSV.")


def build_preview_data(dataframe):
    """Cria a estrutura de pré-visualização a partir do DataFrame processado."""
    if dataframe is None:
        return {"columns": [], "rows": [], "regularization_columns": [], "regularization_rows": []}

    columns_to_show = [col for col in ["logradouro", "logradouro_normalizado"] if col in dataframe.columns]
    regularization_columns = [
        col
        for col in ["logradouro", "logradouro_normalizado", "logradouro_canonico", "similaridade", "frequencia_grupo"]
        if col in dataframe.columns
    ]

    return {
        "columns": columns_to_show,
        "rows": dataframe[columns_to_show].head(20).values.tolist(),
        "regularization_columns": regularization_columns,
        "regularization_rows": dataframe[regularization_columns].head(20).values.tolist(),
    }


def process_upload(request):
    """Processa o upload do arquivo e retorna o formulário para a view."""
    if request.method != "POST":
        return UploadFileForm(), None

    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid():
        return form, None

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
        dataframe = load_dataframe(arquivo)
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

    dataframe_processado = run_preprocessing(dataframe_filtrado)
    request.session["preview_data"] = build_preview_data(dataframe_processado)
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
