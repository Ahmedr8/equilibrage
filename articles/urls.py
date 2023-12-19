from django.urls import path,re_path

from articles import views

urlpatterns = [
    path(r'', views.articles_list),
    re_path(r'^filtred', views.articles_filtred_list),
    re_path(r'^familles$', views.familles_list),
    re_path(r'^familles/filtred', views.familles_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.article_detail),
    re_path(r'^familles/(?P<pk>\w+)$', views.famille_detail)

]