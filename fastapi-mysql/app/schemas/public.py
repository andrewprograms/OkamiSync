from pydantic import BaseModel
from typing import List, Dict, Optional

class SessionStartIn(BaseModel):
    table_token: str
    device_id: str

class SessionStartOut(BaseModel):
    table_id: int
    session_id: str
    session_cap: str
    table_name: str

class AddCartItemIn(BaseModel):
    client_uid: str
    item_id: str
    quantity: int = 1
    options: Dict = {}
    notes: Optional[str] = None

class CartItemOut(BaseModel):
    id: str
    client_uid: str | None = None
    item_id: str
    title: str
    quantity: int
    options: Dict
    notes: Optional[str] = None
    added_by: str
    state: str

class CartOut(BaseModel):
    cart_id: str
    items: List[CartItemOut] = []

class SubmitOut(BaseModel):
    order_id: str
    state: str
