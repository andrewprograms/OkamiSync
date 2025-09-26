from pydantic import BaseModel
from typing import List, Optional

class StaffLoginIn(BaseModel):
    username: str
    password: str

class OrderItemRow(BaseModel):
    id: str
    title: str
    quantity: int
    notes: str | None = None
    state: str

class OrderRow(BaseModel):
    id: str
    table_id: int
    state: str
    items: List[OrderItemRow] = []
    created_at: str
    elapsed_s: int

class ActionIn(BaseModel):
    reason: Optional[str] = None
