from django.shortcuts import render

from .forms import UploadFileForm
from .services.file_loader import process_upload


def home(request):
    if request.GET.get("clear") == "1":
        request.session.pop("preview_data", None)
        request.session.modified = True

    form = UploadFileForm()
    context = {"form": form}
    preview_data = request.session.get("preview_data")
    if preview_data:
        context["preview_data"] = preview_data
    return render(request, "analytics/home.html", context)


def upload_file(request):
    form, response = process_upload(request)

    context = {"form": form}
    preview_data = request.session.get("preview_data")
    if preview_data:
        context["preview_data"] = preview_data

    if response is not None and not preview_data:
        return response

    return render(request, "analytics/home.html", context)