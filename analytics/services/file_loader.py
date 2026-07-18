import os

from django.contrib import messages
from django.shortcuts import redirect

from analytics.forms import UploadFileForm


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

    messages.success(
        request,
        f"Arquivo recebido: {file_info['nome']} | Extensão: {extensao} | Tamanho: {file_info['tamanho_kb']} KB",
    )
    return form, redirect("home")
