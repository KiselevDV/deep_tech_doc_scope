import os

MISTRAL_OCR_URL = os.getenv('MISTRAL_OCR_URL', 'https://api.mistral.com/v1/ocr')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.deepseek.com/v1/chat/completions')
LLM_CLASSIFY_URL = os.getenv('LLM_CLASSIFY_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_TOKEN = os.getenv('LLM_TOKEN')
