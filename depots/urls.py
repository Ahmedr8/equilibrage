from django.urls import path,re_path

from depots import views

urlpatterns = [
    path(r'', views.depots_list),
    re_path(r'^filtred', views.depots_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.depot_detail)
]