import httpx
import json
import logging
import requests

from documents.conf import LLM_CLASSIFY_URL, LLM_TOKEN, LLM_API_URL, LLM_API_KEY


def classify_text_with_llm(text: str) -> str:
    prompt = f'''
    Ты — классификатор страниц технической документации. На основе текста снизу определи тип
    страницы. Возможные типы: сертификат, титульный лист, техническая характеристика, пустая,
    скан без текста, другое. Ответь ТОЛЬКО одним словом на русском языке, без пояснений.
    Текст: {text[:2000]}'''

    try:
        response = requests.post(
            LLM_API_URL,
            json={"prompt": prompt, "max_tokens": 10},
            headers={
                "Authorization": f"Bearer {LLM_TOKEN}" if LLM_TOKEN else "",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("text", "").strip().lower()
    except Exception as e:
        logging.warning(f'Ошибка при вызове LLM: {e}')
        return 'Ошибка'


def extract_materials_from_text(text: str) -> list[dict]:
    prompt = f'''
    Ты — инженер по качеству. Проанализируй следующий текст и извлеки список материалов с их характеристиками.
    Формат ответа:
    [
      {{
        "name": "Сталь 12Х18Н10Т",
        "characteristics": {{
          "ГОСТ": "5632-72",
          "Марка": "12Х18Н10Т",
          "Содержание хрома": "17-19%",
          "Тип": "нержавеющая сталь"
        }}
      }},
      ...
    ]
    Текст: {text[:4000]}  # Обрежем для безопасности'''

    # Пример вызова LLM (DeepSeek или любой другой через API)
    response = call_deepseek_api(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print('LLM вернул невалидный JSON:')
        print(response)
        return []


def call_deepseek_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",  # Зависит от провайдера, например: deepseek-chat, gpt-3.5-turbo, mistral-7b
        "messages": [
            {"role": "system", "content": "Ты — специалист по техдокументации"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = httpx.post(LLM_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f'Ошибка при обращении к LLM API: {e}')
        return ''
