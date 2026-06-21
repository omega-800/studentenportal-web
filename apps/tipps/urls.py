from django.contrib import admin
from django.urls import re_path

from . import views

admin.autodiscover()

app_name = "tipps"

# Dynamic pages
urlpatterns = [
    re_path(r"^$", views.TippList.as_view(), name="tipp_list"),
]
