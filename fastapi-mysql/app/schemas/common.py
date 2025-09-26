from pydantic import BaseModel
from typing import Optional, List, Dict

class I18N(BaseModel):
    en: Optional[str] = None
    ja: Optional[str] = None

class CategoryOut(BaseModel):
    id: str
    title_i18n: Dict[str, str] = {}
    description_i18n: Dict[str, str] = {}
    sort_order: int

class ItemOut(BaseModel):
    id: str
    category_id: str | None = None
    title_i18n: Dict[str, str] = {}
    description_i18n: Dict[str, str] = {}
    price: str
    tax_class: str
    dietary_tags: List[str] = []
    sort_order: int
    image_url: str | None = None
    is_86: bool = False
