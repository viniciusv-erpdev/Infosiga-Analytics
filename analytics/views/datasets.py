from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from analytics.models import DatasetRecordAudit

from analytics.services.dataset_service import DatasetService
import tempfile

import json

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from analytics.services.dataset_search_service import DatasetSearchService

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
    dataset = DatasetService.get_for_user(
        dataset_id,
        request.user,
    )

    if not dataset:
        raise Http404("Dataset não encontrado.")

    search_query = request.GET.get("q", "").strip()
    
    dataset_columns = [
        "id_registro",
        "logradouro",
        "logradouro_limpo",
        "numero_logradouro",
        "logradouro_sugerido",
        "logradouro_canonico",
        "correcao_manual_aplicada",
    ]

    page_obj = None
    audits_by_record = {}
    records_json = []
    load_error = False

    if dataset.resultado_processado:
        try:
            dataframe = DatasetService.load_processed_dataframe(
                dataset
            )

            required_columns = {"id_registro"}
            missing_columns = required_columns - set(dataframe.columns)

            if missing_columns:
                raise ValueError(
                    "O dataset não possui as colunas obrigatórias: "
                    + ", ".join(sorted(missing_columns))
                )

            available_columns = [
                column
                for column in dataset_columns
                if column in dataframe.columns
            ]

            dataframe = dataframe[available_columns].fillna("")

            if search_query:
                dataframe = DatasetSearchService.filter_dataframe(
                    dataframe,
                    search_query,
                )

            records = dataframe.to_dict("records")

            paginator = Paginator(
                records,
                50,
            )

            page_number = request.GET.get(
                "page",
                1,
            )

            page_obj = paginator.get_page(
                page_number
            )

            # IDs dos registros atualmente exibidos
            ids_registros = [
                str(record["id_registro"])
                for record in page_obj.object_list
            ]

            # Busca as auditorias desses registros
            audits = (
                DatasetRecordAudit.objects
                .filter(
                    dataset=dataset,
                    id_registro__in=ids_registros,
                )
                .select_related("usuario")
                .order_by("-created_at")
            )

            # Organiza auditorias por registro
            for audit in audits:
                key = str(
                    audit.id_registro
                )

                audits_by_record.setdefault(
                    key,
                    []
                ).append({
                    "id": audit.id,
                    "field_name": audit.field_name,
                    "previous_value": audit.previous_value,
                    "new_value": audit.new_value,
                    "usuario": str(audit.usuario),
                    "note": audit.note or "",
                    "created_at": audit.created_at.strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                })

            # Vincula as auditorias aos registros da página
            for record in page_obj.object_list:

                record["audits"] = (
                    audits_by_record.get(
                        str(record["id_registro"]),
                        []
                    )
                )

                records_json.append({
                    "id_registro": str(
                        record["id_registro"]
                    ),

                    "logradouro": str(
                        record.get(
                            "logradouro",
                            ""
                        )
                    ),

                    "logradouro_limpo": str(
                        record.get(
                            "logradouro_limpo",
                            ""
                        )
                    ),

                    "numero_logradouro": (
                        None
                        if record.get(
                            "numero_logradouro"
                        ) == ""
                        else record.get(
                            "numero_logradouro"
                        )
                    ),

                    "logradouro_sugerido": str(
                        record.get(
                            "logradouro_sugerido",
                            ""
                        )
                    ),

                    "logradouro_canonico": str(
                        record.get(
                            "logradouro_canonico",
                            ""
                        )
                    ),

                    "correcao_manual_aplicada": bool(
                        record.get(
                            "correcao_manual_aplicada",
                            False
                        )
                    ),

                    "audits": record["audits"],
                })

        except Exception:
            load_error = True

            messages.error(
                request,
                "Não foi possível carregar o resultado processado deste dataset."
            )

    return render(
        request,
        "analytics/datasets/detail.html",
        {
            "dataset": dataset,
            "page_obj": page_obj,
            "dataset_columns": dataset_columns,
            "audits_by_record": audits_by_record,
            "records_json": records_json,
            "search_query": search_query,
            "load_error": load_error,
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

        temporary_file = tempfile.SpooledTemporaryFile(
            max_size=10 * 1024 * 1024,
            suffix=".xlsx",
        )

        dataframe.to_excel(
            temporary_file,
            index=False,
        )

        temporary_file.seek(0)

        filename = (
            f"{Path(dataset.nome_original).stem}_processado.xlsx"
        )

        response = FileResponse(
            temporary_file,
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

@login_required
def dataset_delete(request, dataset_id):

    if request.method != "POST":
        raise Http404("Método não permitido.")

    dataset = DatasetService.get_for_user(
        dataset_id,
        request.user,
    )

    if not dataset:
        raise Http404("Dataset não encontrado.")

    DatasetService.delete(dataset)

    messages.success(
        request,
        "Dataset excluído com sucesso."
    )

    return redirect("dataset_list")

@login_required
@require_POST
def dataset_update_record(request, dataset_id):

    dataset = DatasetService.get_for_user(
        dataset_id,
        request.user,
    )

    if not dataset:
        raise Http404("Dataset não encontrado.")

    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "success": False,
                "error": "Dados inválidos.",
            },
            status=400,
        )

    id_registro = payload.get("id_registro")
    updates = payload.get("updates", {})
    note = payload.get("note", "")

    if not id_registro:
        return JsonResponse(
            {
                "success": False,
                "error": "id_registro é obrigatório.",
            },
            status=400,
        )

    if not isinstance(updates, dict) or not updates:
        return JsonResponse(
            {
                "success": False,
                "error": "Nenhuma alteração informada.",
            },
            status=400,
        )

    try:
        DatasetService.update_record(
            dataset=dataset,
            id_registro=id_registro,
            updates=updates,
            usuario=request.user,
            note=note,
        )

        return JsonResponse({
            "success": True,
            "message": "Registro atualizado com sucesso.",
        })

    except ValueError as exc:
        return JsonResponse(
            {
                "success": False,
                "error": str(exc),
            },
            status=400,
        )

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "error": "Não foi possível atualizar o registro.",
            },
            status=500,
        )

@login_required
@require_GET
def dataset_search_suggestions(request, dataset_id):
    dataset = DatasetService.get_for_user(
        dataset_id,
        request.user,
    )

    if not dataset:
        raise Http404("Dataset não encontrado.")

    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({
            "suggestions": [],
        })

    if not dataset.resultado_processado:
        return JsonResponse({
            "suggestions": [],
        })

    try:
        dataframe = DatasetService.load_processed_dataframe(
            dataset
        )

        suggestions = DatasetSearchService.get_fuzzy_suggestions(
            dataframe,
            query,
        )

        return JsonResponse({
            "suggestions": suggestions,
        })

    except Exception:
        return JsonResponse(
            {
                "suggestions": [],
            },
            status=500,
        )
