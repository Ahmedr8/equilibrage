from .views import SyncFilesView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParamSynchroViewSet

router = DefaultRouter()
router.register(r'param-synchro', ParamSynchroViewSet, basename='param-synchro')
urlpatterns = [
    path('sync/', SyncFilesView.as_view(), name='sync-files'), #http://localhost:8000/sync/
    path('', include(router.urls)), #http://localhost:8000/api/azure/param-synchro/
]