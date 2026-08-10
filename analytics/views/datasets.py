from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from analytics.services.dataset_service import DatasetService


@login_required
def dataset_list(request):
    datasets = DatasetService.list_for_user(
        request.user
    )

    return render(
        request,
        "analytics/datasets/list.html",
        {
            "datasets": datasets,
        },
    )