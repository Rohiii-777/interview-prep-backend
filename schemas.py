from typing import Optional
from pydantic import BaseModel, Field, constr

class CategoryCreate(BaseModel):
    name: constr(min_length=1, max_length=100, strip_whitespace=True)

class CategoryRead(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True   # ✅ Pydantic v2 replaces orm_mode

class QnaBase(BaseModel):
    question: constr(min_length=5, strip_whitespace=True)  # avoid 1-word Qs
    answer: Optional[str] = None
    is_done: Optional[bool] = False
    bookmark: Optional[bool] = False
    category_id: Optional[int] = None

class QnaCreate(QnaBase):
    pass

class QnaUpdate(BaseModel):
    question: Optional[constr(min_length=5, strip_whitespace=True)] = None
    answer: Optional[str] = None
    is_done: Optional[bool] = None
    bookmark: Optional[bool] = None
    category_id: Optional[int] = None

class QnaRead(BaseModel):
    id: int
    question: str
    answer: Optional[str] = None
    is_done: Optional[bool] = False
    bookmark: Optional[bool] = False
    category_id: Optional[int] = None

    class Config:
        from_attributes = True

