from django.urls import path

from .views import home, upload_file
from .review import review_list

urlpatterns = [

    path("", home, name="home"),
    path("upload/", upload_file, name="upload_file"),
    path("review/", review_list, name="review_list"),
]