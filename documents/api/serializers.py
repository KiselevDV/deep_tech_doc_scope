from rest_framework import serializers
from documents.models import Document, Page


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'original_filename']


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'number', 'is_scanned', 'raw_text', 'ocr_text', 'classification', 'created_at',
                  'width', 'height']


class DocumentSerializer(serializers.ModelSerializer):
    pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'original_filename', 'uploaded_at', 'file', 'pages']
