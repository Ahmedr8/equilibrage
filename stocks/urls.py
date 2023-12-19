from django.urls import path,re_path

from stocks import views

urlpatterns = [
    path(r'', views.stocks_list),
    re_path(r'^filtred', views.stocks_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.stock_detail)
]