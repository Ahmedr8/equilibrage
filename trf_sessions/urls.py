from django.urls import path,re_path

from trf_sessions import views

urlpatterns = [
    path(r'', views.sessions_list),
    re_path(r'^filtred', views.sessions_filtred_list),
    re_path(r'^(?P<pk>\w+)$', views.session_detail),
    re_path(r'^details/(?P<pk>\w+)$', views.post_session_detail),
    re_path(r'^props/(?P<pk>\w+)$', views.proposition_affichage)

]