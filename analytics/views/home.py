from django.shortcuts import render

from analytics.forms import UploadFileForm
from analytics.services.file_loader import process_upload


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
    previous_preview_data = request.session.get("preview_data")
    form, response = process_upload(request)

    context = {"form": form}
    preview_data = request.session.get("preview_data")
    if preview_data:
        context["preview_data"] = preview_data

    uploaded_file_info = request.session.get("uploaded_file_info")
    if uploaded_file_info:
        context["uploaded_file_info"] = uploaded_file_info

    if response is not None and not previous_preview_data:
        return response

    return render(request, "analytics/home.html", context)