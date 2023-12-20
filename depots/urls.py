from django.urls import path,re_path

from depots import views

urlpatterns = [
    re_path(r'^page=(?P<page_number>\d+)$', views.depots_list),
    re_path(r'^filtred/page=(?P<page_number>\d+)$', views.depots_filtred_list),
    re_path(r'^delete', views.delete_all_records),
    re_path(r'^(?P<pk>\w+)$', views.depot_detail)
]