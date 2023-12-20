from django.urls import path,re_path

from users import views

urlpatterns = [
    re_path(r'^page_size=settings.PAGINATION_PAGE_SIZE', views.users_list),
    re_path(r'^(?P<pk>\w+)$', views.user_detail)
]