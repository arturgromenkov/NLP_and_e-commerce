import uvicorn
from fastapi import FastAPI

from logger import logger

class PriceDadataAPI(FastAPI):
    def __init__(self) -> None:
        super().__init__()
        # Существующие эндпоинты

def start_api(host, port):
    uvicorn.run(
        app=PriceDadataAPI(),
        host=host,
        port=port
    )