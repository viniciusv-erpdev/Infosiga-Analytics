from django.shortcuts import render

from .forms import UploadFileForm
from .services.file_loader import process_upload


def home(request):
    form = UploadFileForm()
    return render(request, "analytics/home.html", {"form": form})


def upload_file(request):
    form, response = process_upload(request)

    if response is not None:
        return response

    return render(request, "analytics/home.html", {"form": form})