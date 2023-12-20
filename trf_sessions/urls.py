from django.urls import path,re_path

from trf_sessions import views

urlpatterns = [
    re_path(r'^page=(?P<page_number>\d+)$', views.sessions_list),
    re_path(r'^filtred/page=(?P<page_number>\d+)$', views.sessions_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.session_detail),
    re_path(r'^details/(?P<pk>\w+)$', views.post_session_detail),
    re_path(r'^props/(?P<pk>\w+)$', views.proposition_affichage)

]