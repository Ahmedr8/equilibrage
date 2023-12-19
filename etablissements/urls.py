from django.urls import path,re_path

from etablissements import views

urlpatterns = [
    path(r'', views.etablissements_list),
    re_path(r'^filtred', views.etablissements_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.etablissement_detail)
]