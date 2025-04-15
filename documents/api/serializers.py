from django.db.models import Count
from rest_framework import serializers

from documents.models import Document, Page, TextBlock


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'original_filename']


class TextBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = TextBlock
        fields = ['x0', 'y0', 'x1', 'y1', 'text']


class PageSerializer(serializers.ModelSerializer):
    blocks = TextBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ['id', 'number', 'is_scanned', 'raw_text', 'ocr_text', 'classification', 'created_at', 'width',
                  'height', 'blocks']


class DocumentSerializer(serializers.ModelSerializer):
    pages = PageSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'original_filename', 'uploaded_at', 'file', 'pages']


class DocumentStatsSerializer(serializers.ModelSerializer):
    classification_counts = serializers.SerializerMethodField()

    def get_classification_counts(self, obj):
        return (
            obj.pages.values("classification")
            .order_by()
            .annotate(count=Count("classification"))
        )

    class Meta:
        model = Document
        fields = [
            "id", "num_pages", "percent_text", "classification_counts"
        ]
