from django.urls import path

from .views.home import home, upload_file
from analytics.views.review import review_list, review_submit


urlpatterns = [

    path("", home, name="home"),
    path("upload/", upload_file, name="upload_file"),
    path("review/", review_list, name="review_list"),
    path("review/save/", review_submit, name="review_save"),
]