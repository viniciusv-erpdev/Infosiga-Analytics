from django.urls import path

from .views import home, upload_file

urlpatterns = [

    path("", home, name="home"),
    path("upload/", upload_file, name="upload_file"),
]