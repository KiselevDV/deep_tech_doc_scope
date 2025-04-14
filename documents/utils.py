import fitz

from documents.models import Document, Page


# def process_pdf(document: Document):
#     doc_path = document.file.path
#     pdf = fitz.open(doc_path)
#
#     for page_number in range(len(pdf)):
#         page = pdf[page_number]
#         raw_text = page.get_text().strip()
#         is_scanned = len(raw_text) < 10  # эвристика: почти нет текста = скан
#
#         Page.objects.create(
#             document=document,
#             number=page_number + 1,
#             raw_text=raw_text,
#             is_scanned=is_scanned
#         )

def process_pdf(document: Document):
    import fitz
    doc_path = document.file.path
    pdf = fitz.open(doc_path)

    for page_number in range(len(pdf)):
        page_obj = pdf[page_number]
        raw_text = page_obj.get_text().strip()
        is_scanned = len(raw_text) < 10

        page = Page.objects.create(
            document=document,
            number=page_number + 1,
            is_scanned=is_scanned,
            raw_text=raw_text,
            width=page_obj.rect.width,
            height=page_obj.rect.height
        )

        # Парсим текстовые блоки
        for block in page_obj.get_text("blocks"):
            x0, y0, x1, y1, text, *_ = block
            if text.strip():
                TextBlock.objects.create(
                    page=page,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    text=text.strip()
                )
