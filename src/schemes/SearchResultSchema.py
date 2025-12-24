from pydantic import BaseModel
from typing import List

class SearchResultSchema(BaseModel):
    score: float
    text: str
    entity_ids: List[str]
