# import requests

from celery import shared_task
from django.core.files.storage import default_storage

from documents.confs import MISTRAL_API_KEY, MISTRAL_OCR_URL
from documents.models import Document, Page
from documents.utils import process_pdf


@shared_task
def parse_pdf_task(document_id):
    from .models import Document
    doc = Document.objects.get(id=document_id)
    process_pdf(doc)


# @shared_task
# def run_ocr_for_document(document_id):
#     from .models import Document
#
#     doc = Document.objects.get(id=document_id)
#     scanned_pages = doc.pages.filter(is_scanned=True, ocr_text__isnull=True)
#
#     for page in scanned_pages:
#         run_ocr_for_page.delay(page.id)


@shared_task
def run_ocr_for_document(document_id):
    doc = Document.objects.get(id=document_id)
    scanned_pages = doc.pages.filter(is_scanned=True, ocr_text="")

    for page in scanned_pages:
        run_ocr_for_page.delay(page.id)


# @shared_task
# def run_ocr_for_page(page_id):
#     page = Page.objects.get(id=page_id)
#
#     if not page.is_scanned or not page.image:
#         return  # пропустить, если не скан
#
#     with default_storage.open(page.image.name, 'rb') as f:
#         files = {'file': f}
#         headers = {'Authorization': f'Bearer {MISTRAL_API_KEY}'}
#
#         response = requests.post(MISTRAL_OCR_URL, headers=headers, files=files)
#
#         if response.status_code == 200:
#             ocr_result = response.json().get('text')
#             page.ocr_text = ocr_result
#             page.save()
#         else:
#             raise Exception(f"OCR failed: {response.status_code} - {response.text}")


@shared_task
def run_ocr_for_page(page_id):
    page = Page.objects.select_related('document').get(id=page_id)

    if not page.is_scanned:
        return

    doc_path = page.document.file.path
    page_number = page.number  # начинается с 0, если ты сохраняешь так

    pdf = fitz.open(doc_path)
    pdf_page = pdf[page_number]

    # рендерим страницу в PNG
    pix = pdf_page.get_pixmap(dpi=300)
    with tempfile.NamedTemporaryFile(suffix=".png") as temp_image:
        pix.save(temp_image.name)

        with open(temp_image.name, "rb") as image_file:
            files = {"file": image_file}
            headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
            response = requests.post(MISTRAL_OCR_URL, headers=headers, files=files)

        if response.status_code == 200:
            ocr_text = response.json().get("text", "")
            page.ocr_text = ocr_text
            page.save()
        else:
            raise Exception(f"OCR failed: {response.status_code} - {response.text}")
