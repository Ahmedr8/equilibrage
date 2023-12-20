from django.urls import path,re_path

from stocks import views

urlpatterns = [
    re_path(r'^page=(?P<page_number>\d+)$', views.stocks_list),
    re_path(r'^filtred/page=(?P<page_number>\d+)$', views.stocks_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.stock_detail)
]