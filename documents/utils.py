import fitz
import requests

from django.core.cache import cache
from typing import Optional

from documents.conf import LLM_API_URL, LLM_API_KEY
from documents.models import Document, Page, TextBlock


def is_scanned_page(page_obj) -> bool:
    """Проверка, является ли страница сканом с использованием комбинированного подхода"""
    # Быстрые проверки
    raw_text = page_obj.get_text().strip()

    # 1. Проверка на пустую страницу
    if not raw_text:
        return True

    # 2. Проверка структуры документа
    dict_blocks = page_obj.get_text("dict")["blocks"]
    text_blocks = [b for b in dict_blocks if b["type"] == 0 and b.get("text", "").strip()]
    image_blocks = [b for b in dict_blocks if b["type"] == 1]

    # Если есть изображения, покрывающие большую часть страницы
    image_area = sum((b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1]) for b in image_blocks)
    page_area = page_obj.rect.width * page_obj.rect.height
    if page_area > 0 and image_area / page_area > 0.7:
        return True

    # 3. Анализ качества текста
    if looks_like_ocr_artifacts(raw_text):
        return True

    # 4. Использование LLM для сложных случаев
    return check_with_llm_if_needed(page_obj, raw_text)


def looks_like_ocr_artifacts(text: str) -> bool:
    """Проверка текста на типичные артефакты OCR"""
    # Проверка на неправильные пробелы внутри слов
    words = text.split()
    if any(' ' in word and len(word) < 10 for word in words):
        return True

    # Проверка на странные комбинации символов
    common_ocr_errors = ['|', '\\', '/', '[', ']']
    if any(c in text for c in common_ocr_errors):
        return True

    # Проверка соотношения букв и цифр (в сканах часто путают)
    letters = sum(c.isalpha() for c in text)
    digits = sum(c.isdigit() for c in text)
    if digits > 0 and letters > 0 and digits / letters > 0.5:
        return True

    # Проверка на повторяющиеся ошибки
    if count_ocr_errors(text) > len(text.split()) // 10:
        return True

    return False


def count_ocr_errors(text: str) -> int:
    """Подсчет потенциальных ошибок OCR"""
    error_patterns = [
        'vv', 'nn', 'rr', 'qq',  # Частые замены букв
        '1i', 'l1', '0o', 'o0',  # Путаница цифр и букв
        ',,', '..', ';;'  # Дублированные знаки
    ]
    return sum(text.count(pattern) for pattern in error_patterns)


def check_with_llm_if_needed(page_obj, raw_text: str) -> bool:
    """Использование LLM для сложных случаев"""
    # Используем кэш для одинаковых текстов
    cache_key = f"scan_verdict_{hash(raw_text)}"
    if cached := cache.get(cache_key):
        return cached

    # Отправляем только первые 2000 символов для экономии токенов
    prompt = f"""Анализ документа. Это:
    1) Прямой текст из PDF - ответ 'text'
    2) Результат OCR скана - ответ 'scan'
    Критерии:
    - Неестественные пробелы в словах → scan
    - Смешанные буквы и цифры в словах → scan
    - Ошибки в простых словах → scan
    - Чистый текст без артефактов → text
    Текст: {raw_text[:2000]}"""

    try:
        response = requests.post(
            LLM_API_URL,
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
            timeout=5
        )
        verdict = "scan" in response.json()["choices"][0]["message"]["content"].lower()
        cache.set(cache_key, verdict, timeout=3600)
        return verdict
    except Exception:
        # Fallback на эвристику при ошибке
        return default_heuristic_check(page_obj, raw_text)


def default_heuristic_check(page_obj, raw_text: str) -> bool:
    """Эвристическая проверка когда LLM недоступен"""
    word_count = len(raw_text.split())
    avg_word_len = sum(len(word) for word in raw_text.split()) / word_count if word_count else 0

    # Подозрительно короткие или длинные слова
    if 0 < word_count < 10 and (avg_word_len < 2 or avg_word_len > 15):
        return True

    # Проверка площади текста
    dict_blocks = page_obj.get_text("dict")["blocks"]
    text_blocks = [b for b in dict_blocks if b["type"] == 0 and b.get("text", "").strip()]
    text_area = sum((b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1]) for b in text_blocks)
    page_area = page_obj.rect.width * page_obj.rect.height
    if page_area > 0 and text_area / page_area < 0.05:
        return True

    return False


def process_pdf(document: Document):
    """Обработка PDF документа и создание страниц"""
    doc_path = document.file.path
    pdf = fitz.open(doc_path)

    # Создаем все страницы одним запросом
    pages_to_create = []
    text_blocks_to_create = []

    for page_number in range(len(pdf)):
        page_obj = pdf[page_number]
        raw_text = page_obj.get_text().strip()
        is_scanned = is_scanned_page(page_obj)

        page = Page(
            document=document,
            number=page_number + 1,
            is_scanned=is_scanned,
            raw_text=raw_text,
            width=page_obj.rect.width,
            height=page_obj.rect.height
        )
        pages_to_create.append(page)

        # Собираем текстовые блоки
        for block in page_obj.get_text("blocks"):
            x0, y0, x1, y1, text, *_ = block
            if text.strip():
                text_blocks_to_create.append(TextBlock(
                    page=page,  # Ссылка будет установлена после сохранения
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    text=text.strip()
                ))

    # Массовое создание страниц
    created_pages = Page.objects.bulk_create(pages_to_create)

    # Устанавливаем связи для текстовых блоков
    for block, page in zip(text_blocks_to_create, created_pages):
        block.page = page

    # Массовое создание текстовых блоков
    TextBlock.objects.bulk_create(text_blocks_to_create)


def process_document_pages(document, processor, saver, description: Optional[str] = None):
    """Обработка страниц документа с помощью переданных функций"""
    for page in document.pages.all().order_by('number'):
        text = page.raw_text or page.ocr_text
        if not text:
            continue

        result = processor(text)
        saver(page, result)
