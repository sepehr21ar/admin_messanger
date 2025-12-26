from pydantic import BaseModel
from typing import List

class MessageCreate(BaseModel):
    title: str
    content: str
    user_ids: List[int]
