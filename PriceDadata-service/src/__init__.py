import os
import re
import json
import httpx
from typing import List, Dict, Any
from pydantic import BaseModel
from logger import logger

# Если мы найдем меньше 3 главных полей, будем считать, что нужно звать нейросеть (LLM)
MAIN_FIELDS = {"Категория", "Бренд", "Модель"}


# --- Модель для приема данных от фронтенда ---
class ExtractFieldsRequest(BaseModel):
    # По умолчанию тут просто пример для теста
    price_string: str = "Смартфон Apple iPhone 15 Pro 256GB Титановый черный"


# =====================================================================
# ШАГ 1. СЛОВАРИ (Самый быстрый способ)
# Тут мы храним базовые списки синонимов.
# Ключ - правильное название, значение - список того, как могут написать в чеке.
# =====================================================================

MY_CATEGORIES = {
    "Смартфон": ["смартфон", "см-фон", "телефон", "iphone", "айфон", "galaxy"],
    "Телевизор": ["телевизор", "тв", "tv", "smart tv", "led-телевизор"],
    "Ноутбук": ["ноутбук", "нб", "ультрабук", "macbook", "макбук"],
    "Планшет": ["планшет", "ipad", "айпад", "tab "],
    "Стиральная машина": ["стиральная машина", "стир. машина", "см "],
}

MY_BRANDS = {
    "Apple": ["apple", "эпл", "эппл", "iphone", "айфон", "macbook"],
    "Samsung": ["samsung", "самсунг", "galaxy"],
    "Xiaomi": ["xiaomi", "сяоми", "ксиоми", "redmi", "редми", "poco"],
    "ASUS": ["asus", "асус", "vivobook"],
    "LG": ["lg", "элджи"],
    "Sony": ["sony", "сони"],
}

MY_COLORS = {
    "черный": ["черн", "black", "графит", "midnight"],
    "белый": ["бел", "white", "starlight"],
    "серый": ["серый", "grey", "gray"],
    "серебристый": ["серебр", "silver"],
    "красный": ["красн", "red"],
    "синий": ["син", "голуб", "blue"],
    "титановый": ["титан", "titanium"],
}


def find_with_dicts(text: str) -> dict:
    """
    Эта функция ищет совпадения по словарям.
    Работает быстро, поэтому confidence (уверенность) ставим высокую.
    """
    result = {}
    # Переводим всё в нижний регистр, чтобы не зависеть от заглавных букв
    text_lower = text.lower()

    # 1. Ищем категорию
    for cat_name, words in MY_CATEGORIES.items():
        for word in words:
            if word in text_lower:
                result["Категория"] = {"value": cat_name, "confidence": 0.98, "source": "dictionary"}
                break

    # 2. Ищем бренд
    for brand_name, words in MY_BRANDS.items():
        for word in words:
            # Используем простую регулярку, чтобы искать целые слова, а не куски
            if re.search(rf"\b{word}\b", text_lower):
                result["Бренд"] = {"value": brand_name, "confidence": 0.99, "source": "dictionary"}
                break

    # 3. Ищем цвет (можем найти сразу несколько, например "титановый черный")
    found_colors = []
    for color_name, words in MY_COLORS.items():
        for word in words:
            if word in text_lower:
                found_colors.append(color_name)
                break

    if found_colors:
        # Соединяем первые два цвета (если их больше, берем только 2)
        result["Цвет"] = {"value": " ".join(found_colors[:2]), "confidence": 0.95, "source": "dictionary"}

    return result


# =====================================================================
# ШАГ 2. РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ (Regex)
# Тут мы вытаскиваем цифры, память, диагонали и артикулы.
# =====================================================================

def find_with_regex(text: str) -> dict:
    """
    Тут мы ищем паттерны. Уверенность чуть ниже, чем у словарей, т.к. можно зацепить лишнее.
    """
    result = {}

    # 1. Ищем память: ОЗУ/ПЗУ типа "16/512 ГБ" или "2/32GB"
    memory_pattern = re.search(r"(\d{1,2})\s*(?:гб|gb)?\s*/\s*(\d{2,4})\s*(?:гб|gb|тб|tb)", text, re.IGNORECASE)
    if memory_pattern:
        result["Оперативная память"] = {"value": f"{memory_pattern.group(1)} ГБ", "confidence": 0.96, "source": "regex"}
        result["Объем накопителя"] = {"value": f"{memory_pattern.group(2)} ГБ", "confidence": 0.96, "source": "regex"}
    else:
        # Если нет дроби, ищем просто "256GB"
        storage_pattern = re.search(r"(\d{2,4})\s*(гб|gb|тб|tb)", text, re.IGNORECASE)
        if storage_pattern:
            val = storage_pattern.group(1)
            unit = storage_pattern.group(2).upper()  # переводим gb в GB
            if unit == "ГБ" or unit == "GB":
                unit_str = "ГБ"
            else:
                unit_str = "ТБ"
            result["Объем памяти"] = {"value": f"{val} {unit_str}", "confidence": 0.95, "source": "regex"}

    # 2. Ищем диагональ (например 15.6")
    screen_pattern = re.search(r"(\d{1,2}[\.,]?\d{0,2})\s*\"", text)
    if screen_pattern:
        result["Диагональ экрана"] = {"value": f"{screen_pattern.group(1).replace(',', '.')}\"", "confidence": 0.94,
                                      "source": "regex"}

    # 3. Ищем модель (код из больших букв и цифр, минимум 5 символов)
    # Например: DA5B0 или UE50AU7100
    model_pattern = re.search(r"\b([A-Z0-9\-]{5,15})\b", text)
    if model_pattern:
        # Важная проверка: чтобы не спутать модель с памятью (типа 256GB)
        found_val = model_pattern.group(1)
        if not re.match(r"^\d+(GB|TB)$", found_val):
            result["Модель"] = {"value": found_val, "confidence": 0.90, "source": "regex"}

    return result


# =====================================================================
# ШАГ 3. НЕЙРОСЕТЬ (LLM ЗАГЛУШКА)
# Если правила не справились, включаем умный подбор по контексту.
# =====================================================================

async def fake_llm_call(text: str, current_data: dict) -> dict:
    """
    Пока у нас нет API ключа для GPT, эта функция делает вид,
    что она нейросеть, и угадывает данные по контексту текста.
    """
    logger.info("Включаем запасной вариант (LLM Fake) для дозаполнения полей.")
    llm_result = {}
    text_lower = text.lower()

    # Пытаемся угадать категорию
    if "Категория" not in current_data:
        if "гб" in text_lower or "gb" in text_lower:
            llm_result["Категория"] = {"value": "Электроника (Планшет/Смартфон)", "confidence": 0.75, "source": "llm"}

    # Пытаемся вытащить длинное название модели
    if "Модель" not in current_data:
        # разбиваем строку по пробелам
        words = text.split()
        if len(words) > 2:
            # берем второе и третье слово как модель
            llm_result["Модель"] = {"value": f"{words[1]} {words[2]}", "confidence": 0.70, "source": "llm"}

    return llm_result


# =====================================================================
# ГЛАВНЫЙ АЛГОРИТМ (АРБИТРАЖ)
# Сюда приходят запросы из api.py
# =====================================================================

async def extract_fields(request: ExtractFieldsRequest) -> list:
    """
    Функция собирает данные от словарей, регулярок и LLM.
    Потом сортирует их по уверенности.
    """
    raw_text = request.price_string
    if not raw_text:
        return []

    logger.info(f"Начали разбор строки: {raw_text}")

    # 1. Запускаем простые правила
    dict_res = find_with_dicts(raw_text)
    regex_res = find_with_regex(raw_text)

    # Соединяем словари вместе (Regex + Словари)
    all_data = {**regex_res, **dict_res}

    # 2. Проверяем, чего не хватает
    # Смотрим, есть ли в all_data ключи Категория, Бренд, Модель
    missing_fields = MAIN_FIELDS - set(all_data.keys())

    # 3. Если не хватает чего-то важного, вызываем "Нейросеть"
    if len(missing_fields) > 0:
        logger.info(f"Не нашли поля {missing_fields}. Вызываем LLM.")
        llm_res = await fake_llm_call(raw_text, all_data)

        # Добавляем данные от LLM, только если их еще нет
        for key, value in llm_res.items():
            if key not in all_data:
                all_data[key] = value

    # 4. Делаем финальный красивый список
    final_list = []
    for key, item in all_data.items():
        final_list.append({
            "attribute": key,
            "value": item["value"],
            "confidence": item["confidence"],
            "source": item["source"]
        })

    # Сортируем список так, чтобы самые надежные (confidence) были сверху
    final_list.sort(key=lambda x: x["confidence"], reverse=True)

    return final_list