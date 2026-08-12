from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from analytics.services.dataset_service import DatasetService
from io import BytesIO

import os
import tempfile

@login_required
def dataset_list(request):
    datasets = DatasetService.list_for_user(request.user)

    return render(
        request,
        "analytics/datasets/list.html",
        {
            "datasets": datasets,
        },
    )


@login_required
def dataset_detail(request, dataset_id):
    dataset = DatasetService.get_for_user(dataset_id, request.user)
    if not dataset:
        raise Http404("Dataset não encontrado.")

    page_obj = None
    dataset_columns = [
        "logradouro",
        "logradouro_sugerido",
        "logradouro_canonico",
        "correcao_manual_aplicada",
    ]

    if dataset.resultado_processado:
        try:
            dataframe = DatasetService.load_processed_dataframe(dataset)
            dataframe = dataframe[dataset_columns].fillna("")
            records = dataframe.to_dict("records")
            paginator = Paginator(records, 50)
            page_number = request.GET.get("page", 1)
            page_obj = paginator.get_page(page_number)
        except Exception:
            messages.error(request, "Não foi possível carregar o resultado processado deste dataset.")

    return render(
        request,
        "analytics/datasets/detail.html",
        {
            "dataset": dataset,
            "page_obj": page_obj,
            "dataset_columns": dataset_columns,
        },
    )


@login_required
def dataset_download(request, dataset_id):
    dataset = DatasetService.get_for_user(dataset_id, request.user)

    if not dataset:
        raise Http404("Dataset não encontrado.")

    if not dataset.resultado_processado:
        messages.warning(
            request,
            "Este dataset ainda não possui resultado processado."
        )
        return redirect(
            "dataset_detail",
            dataset_id=dataset.id,
        )

    try:
        dataframe = DatasetService.prepare_dataframe_for_export(
            dataset
        )

        temporary_file = tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            delete=False,
        )

        temporary_path = temporary_file.name
        temporary_file.close()

        dataframe.to_excel(
            temporary_path,
            index=False,
        )

        filename = (
            f"{Path(dataset.nome_original).stem}_processado.xlsx"
        )

        file_handle = open(
            temporary_path,
            "rb",
        )

        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=filename,
        )

        response["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )

        return response

    except FileNotFoundError:
        messages.error(
            request,
            "Arquivo de resultado processado não encontrado."
        )

        return redirect(
            "dataset_detail",
            dataset_id=dataset.id,
        )
