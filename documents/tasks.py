import fitz
import requests
import tempfile

from celery import shared_task

from documents.conf import MISTRAL_API_KEY, MISTRAL_OCR_URL
from documents.llm import classify_text_with_llm, extract_materials_from_text
from documents.models import Document, Page, Material
from documents.utils import process_pdf, process_document_pages


@shared_task
def parse_pdf_task(document_id):
    doc = Document.objects.get(id=document_id)
    process_pdf(doc)


@shared_task
def run_ocr_for_document(document_id):
    doc = Document.objects.get(id=document_id)
    scanned_pages = doc.pages.filter(is_scanned=True, ocr_text="")
    for page in scanned_pages:
        run_ocr_for_page.delay(page.id)


@shared_task
def run_ocr_for_page(page_id):
    page = Page.objects.select_related('document').get(id=page_id)
    if not page.is_scanned:
        return
    doc_path = page.document.file.path
    page_number = page.number - 1  # 1-based в модели
    pdf = fitz.open(doc_path)
    pdf_page = pdf[page_number]
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


@shared_task
def classify_document_pages(document_id):
    try:
        document = Document.objects.get(id=document_id)

        def classify(text):
            return classify_text_with_llm(text)

        def save(page, label):
            page.classification = label or "Неизвестно"
            page.save(update_fields=["classification"])

        process_document_pages(document, classify, save, description="classify")

    except Document.DoesNotExist:
        print(f"[classify] Документ {document_id} не найден")


@shared_task
def extract_materials_from_document(document_id):
    try:
        document = Document.objects.get(id=document_id)

        def extract(text):
            return extract_materials_from_text(text)

        def save(page, materials):
            for mat in materials:
                Material.objects.create(
                    page=page,
                    name=mat.get('name', 'Неизвестно'),
                    characteristics=mat.get('characteristics', {})
                )

        process_document_pages(document, extract, save, description="materials")

    except Document.DoesNotExist:
        print(f"[materials] Документ {document_id} не найден")
