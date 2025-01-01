from django.urls import path,re_path

from ventes import views

urlpatterns = [
    re_path(r'^', views.ventes_list),
]