from django.urls import path,re_path

from users import views

urlpatterns = [
    path(r'', views.users_list),
    re_path(r'^(?P<pk>\w+)$', views.user_detail)
]