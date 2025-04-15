from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from documents.models import Document
from documents.tasks import (
    parse_pdf_task, run_ocr_for_document, classify_document_pages, extract_materials_from_document)
from documents.api.serializers import DocumentUploadSerializer, DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser]

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            document.original_filename = document.file.name
            document.save()
            parse_pdf_task.delay(document.id)
            return Response({'id': document.id}, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, pk=None):
        document = self.get_object()
        pages = document.pages.all()
        total = pages.count()
        scanned = pages.filter(is_scanned=True).count()
        text = total - scanned
        return Response({
            "total_pages": total,
            "text_pages": text,
            "scanned_pages": scanned,
            "text_percentage": round((text / total) * 100, 2) if total else 0,
            "scanned_percentage": round((scanned / total) * 100, 2) if total else 0
        })

    @action(detail=True, methods=['post'])
    def run_ocr(self, request, pk=None):
        document = self.get_object()
        run_ocr_for_document.delay(document.id)
        return Response({'status': 'OCR started'})

    @action(detail=True, methods=['post'])
    def run_classification(self, request, pk=None):
        document = self.get_object()
        classify_document_pages.delay(document.id)
        return Response({'status': 'Classification started'})

    @action(detail=True, methods=['post'])
    def extract_materials(self, request, pk=None):
        document = self.get_object()
        extract_materials_from_document.delay(document.id)
        return Response({'status': 'Materials extraction started'})