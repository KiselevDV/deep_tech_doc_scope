from django.urls import path

from documents.api.views import DocumentUploadView, DocumentStatsView


app_name = 'api'

urlpatterns = [
    path('documents/<int:document_id>/stats/', DocumentStatsView.as_view(), name='document-stats'),
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
]
