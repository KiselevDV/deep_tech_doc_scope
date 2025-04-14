from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from documents.tasks import parse_pdf_task, run_ocr_for_document
# from documents.utils import process_pdf
from documents.api.serializers import DocumentUploadSerializer, DocumentSerializer


class DocumentUploadView(APIView):
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            document.original_filename = document.file.name
            document.save()

            # Запускаем парсинг в фоне
            parse_pdf_task.delay(document.id)

            return Response({'id': document.id}, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentStatsView(APIView):
    def get(self, request, document_id):
        document = Document.objects.get(id=document_id)
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


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    @action(detail=True, methods=['post'])
    def run_ocr(self, request, pk=None):
        document = self.get_object()
        run_ocr_for_document.delay(document.id)
        return Response({'status': 'OCR started'})
