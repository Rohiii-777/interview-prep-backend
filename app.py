"""
FastAPI QnA backend (single-file)
Models: Category, QnA
DB: SQLite (db.sqlite)
Features:
- CRUD for categories
- CRUD for qnas (question, answer, is_done, bookmark, category_id)
- List qnas with optional filters (category_id, is_done, bookmark, search)
- Toggle bookmark endpoint
- Toggle/Set is_done endpoint
- CORS enabled for localhost:3000

Run:
1. python -m venv .venv
2. .venv\Scripts\activate (Windows) or source .venv/bin/activate (Unix)
3. pip install fastapi uvicorn sqlalchemy pydantic
4. uvicorn fastapi_qna_backend:app --reload

This single-file app creates the SQLite DB automatically.
"""
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
import os
from fastapi.middleware.cors import CORSMiddleware
DATABASE_URL = "sqlite:///./db.sqlite"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ORM models
class CategoryORM(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    qnas = relationship("QnaORM", back_populates="category", cascade="delete")

class QnaORM(Base):
    __tablename__ = "qnas"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    is_done = Column(Boolean, default=False)
    bookmark = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("CategoryORM", back_populates="qnas")

# Pydantic schemas
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class CategoryRead(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class QnaBase(BaseModel):
    question: str = Field(..., min_length=1)
    answer: Optional[str] = None
    is_done: Optional[bool] = False
    bookmark: Optional[bool] = False
    category_id: Optional[int] = None

class QnaCreate(QnaBase):
    pass

class QnaUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    is_done: Optional[bool] = None
    bookmark: Optional[bool] = None
    category_id: Optional[int] = None

class QnaRead(QnaBase):
    id: int
    class Config:
        orm_mode = True

# Create DB
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="QnA Backend - FastAPI")

# Allow CORS for local dev (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

# Category endpoints
@app.post("/categories/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(CategoryORM).filter(CategoryORM.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    db_cat = CategoryORM(name=category.name)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@app.get("/categories/", response_model=List[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(CategoryORM).all()

@app.get("/categories/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(CategoryORM).get(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat

@app.put("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryCreate, db: Session = Depends(get_db)):
    cat = db.query(CategoryORM).get(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = payload.name
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(CategoryORM).get(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return None

# QnA endpoints
@app.post("/qnas/", response_model=QnaRead, status_code=status.HTTP_201_CREATED)
def create_qna(payload: QnaCreate, db: Session = Depends(get_db)):
    if payload.category_id:
        cat = db.query(CategoryORM).get(payload.category_id)
        if not cat:
            raise HTTPException(status_code=400, detail="category_id does not exist")
    db_q = QnaORM(
        question=payload.question,
        answer=payload.answer,
        is_done=payload.is_done or False,
        bookmark=payload.bookmark or False,
        category_id=payload.category_id,
    )
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q

@app.get("/qnas/", response_model=List[QnaRead])
def list_qnas(
    category_id: Optional[int] = None,
    is_done: Optional[bool] = None,
    bookmark: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(QnaORM)
    if category_id is not None:
        query = query.filter(QnaORM.category_id == category_id)
    if is_done is not None:
        query = query.filter(QnaORM.is_done == is_done)
    if bookmark is not None:
        query = query.filter(QnaORM.bookmark == bookmark)
    if search:
        like = f"%{search}%"
        query = query.filter((QnaORM.question.ilike(like)) | (QnaORM.answer.ilike(like)))
    return query.order_by(QnaORM.id.desc()).all()

@app.get("/qnas/{qna_id}", response_model=QnaRead)
def get_qna(qna_id: int, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    return q

@app.put("/qnas/{qna_id}", response_model=QnaRead)
def update_qna(qna_id: int, payload: QnaUpdate, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    if payload.question is not None:
        q.question = payload.question
    if payload.answer is not None:
        q.answer = payload.answer
    if payload.is_done is not None:
        q.is_done = payload.is_done
    if payload.bookmark is not None:
        q.bookmark = payload.bookmark
    if payload.category_id is not None:
        if payload.category_id:
            cat = db.query(CategoryORM).get(payload.category_id)
            if not cat:
                raise HTTPException(status_code=400, detail="category_id does not exist")
        q.category_id = payload.category_id
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@app.delete("/qnas/{qna_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qna(qna_id: int, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    db.delete(q)
    db.commit()
    return None

@app.patch("/qnas/{qna_id}/bookmark", response_model=QnaRead)
def toggle_bookmark(qna_id: int, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    q.bookmark = not q.bookmark
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@app.patch("/qnas/{qna_id}/mark", response_model=QnaRead)
def set_done(qna_id: int, done: bool, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    q.is_done = done
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

# Quick root
@app.get("/")
def root():
    return {"msg": "QnA backend up. Open /docs for API docs."}
