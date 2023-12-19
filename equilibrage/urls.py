
from django.urls import re_path,include
from django.contrib import admin

urlpatterns = [
    re_path(r'^articles/', include('articles.urls')),
    re_path(r'^etablissements/', include('etablissements.urls')),
    re_path(r'^depots/', include('depots.urls')),
    re_path(r'^stocks/', include('stocks.urls')),
    re_path(r'^users/', include('users.urls')),
    re_path(r'^sessions/', include('trf_sessions.urls')),
    re_path(r'^admin/', admin.site.urls),
]
