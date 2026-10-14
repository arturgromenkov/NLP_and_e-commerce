"""
Экстрактор атрибутов на основе правил и регулярных выражений.
Извлекает бренды, память, диагональ, цвет из title и description.
"""
import re
from typing import Dict, Tuple, Optional


class RuleExtractor:
    def __init__(self):
        # Словарь популярных брендов
        self.brands = [
            'Samsung', 'Apple', 'Xiaomi', 'Sony', 'LG', 'Bosch', 'Philips',
            'Hisense', 'Panasonic', 'GSS', 'SSG', 'UNIMALL', 'Coolfort',
            'Vixter', 'Haylou', 'PANiN', 'Enio', 'PrintyFull'
        ]
        brand_pattern = r'\b(' + '|'.join(self.brands) + r')\b'
        self.brand_regex = re.compile(brand_pattern, re.IGNORECASE)
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Очищает текст от HTML-тегов и нормализует пробелы"""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_brand(self, title: str, description: str) -> Tuple[Optional[str], float]:
        """Извлекает бренд. Сначала ищем в title, потом в description"""
        title_clean = self.clean_text(title)
        desc_clean = self.clean_text(description)
        
        match = self.brand_regex.search(title_clean)
        if match:
            return match.group(1).title(), 0.98
        
        match = self.brand_regex.search(desc_clean)
        if match:
            return match.group(1).title(), 0.85
        
        return None, 0.0
    
    def extract_memory(self, title: str, description: str) -> Tuple[Optional[str], float]:
        """Извлекает объём памяти (ГБ/GB)"""
        text = f"{self.clean_text(title)} {self.clean_text(description)}"
        match = re.search(r'(\d+)\s*(гб|gb|гигабайт)', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} ГБ", 0.95
        return None, 0.0
    
    def extract_diagonal(self, title: str, description: str) -> Tuple[Optional[str], float]:
        """Извлекает диагональ экрана"""
        text = f"{self.clean_text(title)} {self.clean_text(description)}"
        match = re.search(r'(\d+[\.,]\d+)\s*["\'дюйм]', text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '.')
            return f"{value} дюйма", 0.90
        return None, 0.0
    
    def extract_color(self, title: str, description: str) -> Tuple[Optional[str], float]:
        """Извлекает цвет товара"""
        text = f"{self.clean_text(title)} {self.clean_text(description)}".lower()
        colors_map = {
            'черный': 'Чёрный', 'чёрный': 'Чёрный', 'black': 'Чёрный',
            'белый': 'Белый', 'white': 'Белый',
            'синий': 'Синий', 'blue': 'Синий',
            'розовый': 'Розовый', 'pink': 'Розовый',
        }
        for key, canonical in colors_map.items():
            if re.search(rf'\b{key}\b|цвет[:\s]+{key}', text):
                return canonical, 0.80
        return None, 0.0
    
    def extract_all(self, row: Dict) -> Dict:
        """Главный метод: извлекает все атрибуты из одной карточки"""
        title = row.get('title', '')
        description = row.get('description', '')
        
        results = {}
        
        for attr_name, method in [
            ('Бренд', self.extract_brand),
            ('Объём памяти', self.extract_memory),
            ('Диагональ', self.extract_diagonal),
            ('Цвет', self.extract_color),
        ]:
            value, confidence = method(title, description)
            if value:
                results[attr_name] = {
                    'value': value,
                    'confidence': confidence,
                    'source': 'rule_extractor'
                }
        
        return results