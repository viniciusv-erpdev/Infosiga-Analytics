from django.urls import path

from analytics.views.auth import CustomLoginView, CustomLogoutView, register
from analytics.views.home import home, upload_file
from analytics.views.review import review_list, review_submit
from analytics.views.datasets import dataset_list

urlpatterns = [
    path("", home, name="home"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("upload/", upload_file, name="upload_file"),
    path("review/", review_list, name="review_list"),
    path("review/save/", review_submit, name="review_save"),
    path("datasets/", dataset_list, name="dataset_list"),
]