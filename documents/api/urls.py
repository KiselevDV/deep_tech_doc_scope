from django.urls import path, include
from rest_framework.routers import DefaultRouter
from documents.api.views import DocumentViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
