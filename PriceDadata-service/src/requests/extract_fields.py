from typing import List, Dict, Any, Optional, Tuple, Union
import asyncio
import httpx
from pydantic import BaseModel
from logger import logger

class ExtractFieldsRequest(BaseModel):
    price_string: str = None

async def extract_fields(
    request: ExtractFieldsRequest,
) -> List[Dict[str, Any]]:
    return 0
