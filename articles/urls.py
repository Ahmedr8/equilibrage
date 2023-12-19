from django.urls import path,re_path

from articles import views

urlpatterns = [
    path(r'', views.articles_list),
    re_path(r'^filtred', views.articles_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.article_detail),

]