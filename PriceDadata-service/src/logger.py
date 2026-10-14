import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Попытка импорта настроек Graylog
try:
    from settings import GRAYLOG_HOST, GRAYLOG_PORT
except ImportError:
    # Если файла settings нет, берём из переменных окружения
    GRAYLOG_HOST = os.getenv('GRAYLOG_HOST')
    GRAYLOG_PORT = os.getenv('GRAYLOG_PORT')

# Создаём логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --- Кастомный форматтер для консоли ---
class DetailedFormatter(logging.Formatter):
    def format(self, record):
        # Добавляем миллисекунды к asctime
        record.asctime = self.formatTime(record, self.datefmt) + f'.{int(record.msecs):03d}'
        # Базовое сообщение
        base_msg = super().format(record)
        # Если есть extra-поля (кроме стандартных), добавляем их в конец
        extra = {k: v for k, v in record.__dict__.items() 
                 if k not in logging.LogRecord.__dict__ and not k.startswith('_')}
        if extra:
            extra_str = ' '.join(f'{k}={v}' for k, v in extra.items())
            return f'{base_msg} ({extra_str})'
        return base_msg

# Настройка форматтера для консоли
console_formatter = DetailedFormatter(
    fmt='%(asctime)s - %(levelname)-8s - %(name)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Консольный обработчик
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# --- Graylog (как у вас, только добавил проверку порта) ---
if GRAYLOG_HOST and GRAYLOG_PORT:
    try:
        import graypy
        port = int(GRAYLOG_PORT)
        # Используем UDP-хендлер для производительности (можно заменить на HTTP)
        graylog_handler = graypy.GELFUDPHandler(
            host=GRAYLOG_HOST,
            port=port,
            facility='civitiai_service'
        )
        graylog_handler.setLevel(logging.INFO)
        logger.addHandler(graylog_handler)
        logger.info(f"Graylog logging enabled (host: {GRAYLOG_HOST}:{port})")
    except ImportError:
        logger.warning("Graylog logging unavailable: graypy library not installed")
    except ValueError:
        logger.warning(f"Graylog logging unavailable: invalid port '{GRAYLOG_PORT}'")
    except Exception as e:
        logger.warning(f"Graylog logging unavailable: {e}")
else:
    logger.debug("Graylog not configured (set GRAYLOG_HOST and GRAYLOG_PORT to enable)")