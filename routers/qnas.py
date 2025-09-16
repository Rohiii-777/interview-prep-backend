from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models import QnaORM, CategoryORM
from schemas import QnaCreate, QnaRead, QnaUpdate
from typing import List, Optional
from sqlalchemy import text
from services.search import simple_search
# from services.embeddings import add_to_index, update_in_index, remove_from_index,semantic_search

router = APIRouter(prefix="/qnas", tags=["QnAs"])

@router.post("/", response_model=QnaRead, status_code=status.HTTP_201_CREATED)
def create_qna(payload: QnaCreate, db: Session = Depends(get_db)):
    if payload.category_id:
        cat = db.query(CategoryORM).get(payload.category_id)
        if not cat:
            raise HTTPException(status_code=400, detail="category_id does not exist")

    db_q = QnaORM(**payload.dict())

    if payload.answer:
        db_q.answer = format_answer(payload.answer)   # ✅ fixed

    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    # add_to_index(db_q)
    return db_q


import re

def detect_language(answer: str) -> str:
    """
    Guess language based on keywords.
    """
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b", answer, re.I):
        return "sql"
    if re.search(r"\b(def |class |import |print\()", answer):
        return "python"
    if re.search(r"\b(function|const|let|var|console\.log)\b", answer):
        return "javascript"
    if re.search(r"#include|int main|std::", answer):
        return "cpp"
    if re.search(r"public class|System\.out\.println", answer):
        return "java"
    return "plaintext"  # fallback

def format_answer(answer: str) -> str:
    """
    Wrap code answers in Markdown with language highlighting.
    """
    # If already contains Markdown code block, don't touch
    if "```" in answer:
        return answer.strip()

    # If answer looks like code (multiple lines / braces / keywords)
    if re.search(r"\n", answer) or re.search(r"(SELECT|def |function )", answer):
        lang = detect_language(answer)
        return f"```{lang}\n{answer.strip()}\n```"

    return answer.strip()

@router.get("/", response_model=List[QnaRead])
def list_qnas(
    category_id: Optional[int] = None,
    is_done: Optional[bool] = None,
    bookmark: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    # Semantic search first
    if search:
        results = None
        # results = semantic_search(search, db, top_k=limit)
        if results:   # ✅ semantic found results
            return results
        # fallback to LIKE if semantic empty
        return simple_search(db, search)[skip: skip+limit]

    # No search → just normal filtering
    query = db.query(QnaORM)
    if category_id is not None:
        query = query.filter(QnaORM.category_id == category_id)
    if is_done is not None:
        query = query.filter(QnaORM.is_done == is_done)
    if bookmark is not None:
        query = query.filter(QnaORM.bookmark == bookmark)

    return query.order_by(QnaORM.id.desc()).offset(skip).limit(limit).all()


@router.get("/{qna_id}", response_model=QnaRead)
def get_qna(qna_id: int, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    return q

@router.put("/{qna_id}", response_model=QnaRead)
def update_qna(qna_id: int, payload: QnaUpdate, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")

    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        if field == "answer" and value is not None:
            q.answer = format_answer(value)   # ✅ ensure Markdown/code wrapping
        else:
            setattr(q, field, value)

    db.commit()
    db.refresh(q)
    # update_in_index(q)
    return q



@router.delete("/{qna_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qna(qna_id: int, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    db.delete(q)
    db.commit()
    # remove_from_index(q.id)

@router.patch("/{qna_id}/bookmark", response_model=QnaRead)
def toggle_bookmark(qna_id: int, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    q.bookmark = not q.bookmark
    db.commit()
    db.refresh(q)
    return q

@router.patch("/{qna_id}/mark", response_model=QnaRead)
def set_done(qna_id: int, done: bool, db: Session = Depends(get_db)):
    q = db.query(QnaORM).get(qna_id)
    if not q:
        raise HTTPException(status_code=404, detail="QnA not found")
    q.is_done = done
    db.commit()
    db.refresh(q)
    return q
