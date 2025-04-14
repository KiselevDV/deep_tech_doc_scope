from django.urls import path, include


app_name = 'documents'

urlpatterns = [
    path('api/', include('documents.api.urls')),
]
