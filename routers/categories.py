from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models import CategoryORM
from schemas import CategoryCreate, CategoryRead
from typing import List

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(CategoryORM).filter(CategoryORM.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    db_cat = CategoryORM(name=category.name)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.get("/", response_model=List[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(CategoryORM).all()

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(CategoryORM).get(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat

@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryCreate, db: Session = Depends(get_db)):
    cat = db.query(CategoryORM).get(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat.name = payload.name
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(CategoryORM).get(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
