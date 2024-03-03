from django.urls import path,re_path

from etablissements import views

urlpatterns = [
    re_path(r'^page=(?P<page_number>\d+)$', views.etablissements_list),
    re_path(r'^filtred/page=(?P<page_number>\d+)$', views.etablissements_filtred_list),
    re_path(r'^delete', views.delete_all_records),
    re_path(r'^all', views.get_all_records),
    re_path(r'^(?P<pk>\w+)$', views.etablissement_detail)
]