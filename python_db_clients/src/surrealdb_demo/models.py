from pydantic import BaseModel
from typing import List, Optional

class Article(BaseModel):
    id: Optional[str] = None
    title: str
    published: bool
    tags: List[str] = []
