from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from analytics.forms import UploadFileForm
from analytics.services.dataset_service import DatasetService
from analytics.services.file_loader import process_upload


@login_required
def home(request):
    if request.GET.get("clear") == "1":
        request.session.pop("last_dataset_id", None)
        request.session.pop("uploaded_file_info", None)
        request.session.modified = True

    form = UploadFileForm()
    context = {"form": form}

    last_dataset_id = request.session.get("last_dataset_id")
    if last_dataset_id:
        new_dataset = DatasetService.get_for_user(last_dataset_id, request.user)
        if new_dataset:
            context["new_dataset"] = new_dataset

    uploaded_file_info = request.session.get("uploaded_file_info")
    if uploaded_file_info:
        context["uploaded_file_info"] = uploaded_file_info

    return render(request, "analytics/home.html", context)


@login_required
def upload_file(request):
    form, response = process_upload(request)

    context = {"form": form}

    last_dataset_id = request.session.get("last_dataset_id")
    if last_dataset_id:
        new_dataset = DatasetService.get_for_user(last_dataset_id, request.user)
        if new_dataset:
            context["new_dataset"] = new_dataset

    uploaded_file_info = request.session.get("uploaded_file_info")
    if uploaded_file_info:
        context["uploaded_file_info"] = uploaded_file_info

    if response is not None:
        return response

    return render(request, "analytics/home.html", context)