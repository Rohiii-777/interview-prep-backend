from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import QnaORM, CategoryORM
from schemas import QnaRead
import json
import csv
from io import StringIO

router = APIRouter(prefix="/bulk", tags=["Bulk Import/Export"])

# ✅ Export all QnAs as JSON
@router.get("/export/json")
def export_qnas_json(db: Session = Depends(get_db)):
    qnas = db.query(QnaORM).all()
    return [QnaRead.from_orm(q).dict() for q in qnas]


# ✅ Export all QnAs as CSV
@router.get("/export/csv")
def export_qnas_csv(db: Session = Depends(get_db)):
    qnas = db.query(QnaORM).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "question", "answer", "is_done", "bookmark", "category_id"])

    for q in qnas:
        writer.writerow([q.id, q.question, q.answer, q.is_done, q.bookmark, q.category_id])

    return {"csv": output.getvalue()}


# ✅ Import QnAs from JSON file
@router.post("/import/json")
async def import_qnas_json(file: UploadFile, db: Session = Depends(get_db)):
    try:
        data = json.load(file.file)
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        for item in data:
            q = QnaORM(**{k: v for k, v in item.items() if k in ["question", "answer", "is_done", "bookmark", "category_id"]})
            db.add(q)
        db.commit()
        return {"status": "success", "imported": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Import QnAs from CSV file
@router.post("/import/csv")
async def import_qnas_csv(file: UploadFile, db: Session = Depends(get_db)):
    try:
        content = (await file.read()).decode("utf-8")
        reader = csv.DictReader(StringIO(content))
        count = 0
        for row in reader:
            q = QnaORM(
                question=row["question"],
                answer=row.get("answer"),
                is_done=row.get("is_done", "False").lower() == "true",
                bookmark=row.get("bookmark", "False").lower() == "true",
                category_id=int(row["category_id"]) if row.get("category_id") else None,
            )
            db.add(q)
            count += 1
        db.commit()
        return {"status": "success", "imported": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
