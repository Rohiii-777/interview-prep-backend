from sqlalchemy.orm import Session
from models import QnaORM

def simple_search(db: Session, search: str):
    like = f"%{search}%"
    return db.query(QnaORM).filter(
        (QnaORM.question.ilike(like)) | (QnaORM.answer.ilike(like))
    ).all()
