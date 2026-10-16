import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Подтягиваем логгер
from logger import logger

# Импортируем нашу логику из соседнего файла
from __init__ import extract_fields, ExtractFieldsRequest

# Создаем приложение FastAPI и сразу переносим Swagger UI на главную страницу (/)
app = FastAPI(
    title="Студенческий парсер М.Видео",
    description="Разбираем чеки гибридным методом: Словари, Регулярки и Фоллбэк.",
    version="1.0.0",
    docs_url="/"  # Убрали /docs, теперь открывается прямо на 127.0.0.1:8080/
)


# --- Схемы данных (Pydantic) ---

class AttributeModel(BaseModel):
    """
    Как выглядит один распарсенный атрибут.
    """
    attribute: str  # Имя (Например: Цвет)
    value: str  # Значение (Например: Черный)
    confidence: float  # Уверенность (Например: 0.95)
    source: str  # Откуда взяли (dictionary, regex или llm)


class FinalResponse(BaseModel):
    """
    Как выглядит весь ответ нашего сервера.
    """
    status: str
    input_text: str
    attributes: List[AttributeModel]


# --- Эндпоинты ---

@app.post("/extract", response_model=FinalResponse)
async def process_request(request: ExtractFieldsRequest):
    """
    Этот эндпоинт принимает JSON от фронтенда со строкой price_string.
    """
    logger.info("Кто-то дернул ручку /extract")

    # Вызываем нашу большую функцию из __init__.py
    results = await extract_fields(request)

    # Формируем ответ, превращая словари в Pydantic модели
    my_attributes = []
    for item in results:
        attr_obj = AttributeModel(
            attribute=item["attribute"],
            value=item["value"],
            confidence=item["confidence"],
            source=item["source"]
        )
        my_attributes.append(attr_obj)

    # Отдаем ответ пользователю
    return FinalResponse(
        status="success",
        input_text=request.price_string,
        attributes=my_attributes
    )


# --- Запуск ---

def start_api(host: str, port: int):
    """
    Функция запускает сервер Uvicorn. Вызывается из app.py
    """
    logger.info(f"Стартуем сервер на {host}:{port}")
    uvicorn.run(app, host=host, port=port)