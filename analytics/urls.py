from django.urls import path

from analytics.views.auth import CustomLoginView, CustomLogoutView, register
from analytics.views.home import home, upload_file
from analytics.views.review import review_list, review_submit
from analytics.views.datasets import (
    dataset_list,
    dataset_detail,
    dataset_download,
    dataset_delete,
    dataset_update_record,
    dataset_search_suggestions,)

urlpatterns = [
    path("", home, name="home"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("upload/", upload_file, name="upload_file"),
    path("review/", review_list, name="review_list"),
    path("review/save/", review_submit, name="review_save"),
    path("datasets/", dataset_list, name="dataset_list"),
    path("datasets/<int:dataset_id>/", dataset_detail, name="dataset_detail"),
    path("datasets/<int:dataset_id>/sugestoes/",dataset_search_suggestions,name="dataset_search_suggestions",),
    path("datasets/<int:dataset_id>/download/", dataset_download, name="dataset_download"),
    path("datasets/<int:dataset_id>/excluir/",dataset_delete,name="dataset_delete",),
    path("datasets/<int:dataset_id>/editar/", dataset_update_record,name="dataset_update_record",),
    path("datasets/<int:dataset_id>/sugestoes/",dataset_search_suggestions,name="dataset_search_suggestions",),
    ]