from fastapi import APIRouter, HTTPException, Depends
import os, requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from db import get_db
from models import QnaORM


load_dotenv()
router = APIRouter(prefix="/ai", tags=["AI"])

HF_TOKEN = os.getenv("HF_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

HF_SUMMARIZER = "facebook/bart-large-cnn"


@router.post("/summarize/{qna_id}")
def summarize_qna(qna_id: int, db: Session = Depends(get_db)):
    """
    Summarize an existing QnA answer into a shorter version using HuggingFace Bart.
    """
    qna = db.query(QnaORM).get(qna_id)
    if not qna or not qna.answer:
        raise HTTPException(status_code=404, detail="QnA not found or has no answer")

    if not HF_TOKEN:
        raise HTTPException(status_code=501, detail="HF_API_TOKEN missing, summarization disabled")

    payload = {"inputs": qna.answer}
    url = f"https://api-inference.huggingface.co/models/{HF_SUMMARIZER}"
    res = requests.post(url, headers=HEADERS, json=payload, timeout=60)

    if res.status_code != 200:
        raise HTTPException(status_code=500, detail=f"HuggingFace error: {res.text}")

    output = res.json()
    if isinstance(output, list) and "summary_text" in output[0]:
        return {
            "qna_id": qna_id,
            "original_answer": qna.answer,
            "summary": output[0]["summary_text"].strip(),
        }

    raise HTTPException(status_code=500, detail=f"Unexpected HF output: {output}")
