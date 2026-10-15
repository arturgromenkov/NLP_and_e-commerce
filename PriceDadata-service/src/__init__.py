from typing import List, Dict, Any
from pydantic import BaseModel

class ExtractFieldsRequest(BaseModel):
    """Модель входящего запроса. Ждем строку с чеком или описанием."""
    price_string: str = None

async def extract_fields(
    request: ExtractFieldsRequest,
) -> List[Dict[str, Any]]:
    """
    Асинхронная функция гибридного извлечения (Regex + словари + LLM).
    В будущем здесь будет написан весь наш NLP-пайплайн.
    Сейчас это заглушка, чтобы не ломать запуск сервера.
    """
    return [{"status": "mock data"}]