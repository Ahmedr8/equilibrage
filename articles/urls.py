from django.urls import path,re_path

from articles import views

urlpatterns = [
    re_path(r'^page=(?P<page_number>\d+)$', views.articles_list),
    re_path(r'^filtred/page=(?P<page_number>\d+)$', views.articles_filtred_list),
    re_path(r'^delete', views.delete_all_records),
    re_path(r'^generique/page=(?P<page_number>\d+)$', views.articles_gen_list),
    re_path(r'^generique/filtred/page=(?P<page_number>\d+)$', views.articles_gen_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.article_detail),

]