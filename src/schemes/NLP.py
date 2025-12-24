from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    text: str
    limit: Optional[int] = 5