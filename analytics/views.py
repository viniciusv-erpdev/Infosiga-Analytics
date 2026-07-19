from django.shortcuts import render

from .forms import UploadFileForm
from .services.file_loader import load_dataframe, process_upload
from .services.filters import apply_filters
from .services.preprocessing.pipeline import run_preprocessing


def home(request):
    if request.GET.get("clear") == "1":
        request.session.pop("preview_data", None)
        request.session.pop("uploaded_file_info", None)
        request.session.modified = True

    form = UploadFileForm()
    context = {"form": form}
    preview_data = request.session.get("preview_data")
    if preview_data:
        context["preview_data"] = preview_data

    uploaded_file_info = request.session.get("uploaded_file_info")
    if uploaded_file_info:
        context["uploaded_file_info"] = uploaded_file_info

    return render(request, "analytics/home.html", context)


def upload_file(request):
    form, response = process_upload(request)

    context = {"form": form}
    preview_data = request.session.get("preview_data")
    if preview_data:
        context["preview_data"] = preview_data

    uploaded_file_info = request.session.get("uploaded_file_info")
    if uploaded_file_info:
        context["uploaded_file_info"] = uploaded_file_info

    if request.method == "POST" and request.FILES.get("arquivo"):
        try:
            dataframe = load_dataframe(request.FILES["arquivo"])
            tipo_via = request.POST.get("tipo_via")
            tipo_sinistro = request.POST.get("tipo_sinistro")
            dataframe_filtrado = apply_filters(dataframe, tipo_via=tipo_via, tipo_sinistro=tipo_sinistro)
            dataframe_processado = run_preprocessing(dataframe_filtrado)

            columns_to_show = ["logradouro", "logradouro_normalizado"]
            if "logradouro" in dataframe_processado.columns and "logradouro_normalizado" in dataframe_processado.columns:
                request.session["preview_data"] = {
                    "columns": columns_to_show,
                    "rows": dataframe_processado[columns_to_show].head(20).values.tolist(),
                }
                request.session.modified = True
                context["preview_data"] = request.session["preview_data"]
        except Exception:
            pass

    if response is not None and not preview_data:
        return response

    return render(request, "analytics/home.html", context)