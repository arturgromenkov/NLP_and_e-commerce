import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Подтягиваем кастомный логгер, который написали коллеги
from logger import logger

# Импортируем функцию-заглушку и модель запроса
# Используем __init__, так как точка входа app.py запускается из этой же папки
from __init__ import extract_fields, ExtractFieldsRequest

# Инициализируем приложение FastAPI (Оно и будет нашим API)
app = FastAPI(title="M.Video Attribute Extraction API")


# --- Pydantic модели для строгого ответа API ---

class Attribute(BaseModel):
    """Модель одного извлеченного атрибута (например: Бренд - Samsung)"""
    attribute: str
    value: str
    confidence: float


class ExtractionResponse(BaseModel):
    """Главная модель ответа, которая возвращает статус и список атрибутов"""
    status: str
    attributes: List[Attribute]


# --- Роуты (Эндпоинты) API ---

@app.post("/extract", response_model=ExtractionResponse)
async def process_extraction(request: ExtractFieldsRequest):
    """
    Главный эндпоинт для извлечения атрибутов из строки.
    Пока реальной логики нет, возвращаем красивый Mock JSON (заглушку),
    чтобы команда фронтенда могла начать делать интерфейс.
    """
    logger.info(f"Получен запрос на извлечение: {request.price_string}")

    # Имитируем вызов реальной функции извлечения (результат пока игнорируем)
    _ = await extract_fields(request)

    # Тестовые данные для демонстрации на чекпоинте
    fake_data = [
        Attribute(attribute="Бренд", value="Samsung", confidence=0.98),
        Attribute(attribute="Цвет", value="черный", confidence=0.81)
    ]

    # Возвращаем JSON в правильном формате
    return ExtractionResponse(status="success", attributes=fake_data)


# --- Функция запуска ---

def start_api(host: str, port: int):
    """
    Эта функция вызывается из файла app.py.
    Она берет настройки из .env и поднимает сервер через uvicorn.
    """
    logger.info(f"Запуск API сервера на {host}:{port}")
    uvicorn.run(app, host=host, port=port)