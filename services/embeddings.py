import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from models import QnaORM

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")
embedding_dim = model.get_sentence_embedding_dimension()
id_map = {}
# FAISS index + mapping
index = faiss.IndexIDMap(faiss.IndexFlatL2(embedding_dim))

def semantic_search(query: str, db: Session, top_k: int = 5):
    """
    Run semantic search on FAISS index.
    """
    if index.ntotal == 0:
        build_index(db)

    q_emb = model.encode([query], convert_to_numpy=True)
    D, I = index.search(q_emb, top_k)

    ids = [id_map[i] for i in I[0] if i in id_map]
    if not ids:
        return []

    return db.query(QnaORM).filter(QnaORM.id.in_(ids)).all()

def build_index(db: Session):
    """
    Rebuild the whole FAISS index from DB.
    """
    index.reset()
    qnas = db.query(QnaORM).all()
    if not qnas:
        return
    texts = [f"{q.question} {q.answer or ''}" for q in qnas]
    embeddings = model.encode(texts, convert_to_numpy=True)
    ids = np.array([q.id for q in qnas])
    index.add_with_ids(embeddings, ids)

def add_to_index(qna: QnaORM):
    """
    Add a single QnA to FAISS.
    """
    text = f"{qna.question} {qna.answer or ''}"
    emb = model.encode([text], convert_to_numpy=True)
    index.add_with_ids(emb, np.array([qna.id]))

def update_in_index(qna: QnaORM):
    """
    Remove old entry & re-add updated one.
    """
    remove_from_index(qna.id)
    add_to_index(qna)

def remove_from_index(qna_id: int):
    """
    Delete from FAISS by ID.
    """
    index.remove_ids(np.array([qna_id]))

def semantic_search(query: str, db: Session, top_k: int = 5):
    """
    Search FAISS index.
    """
    if index.ntotal == 0:
        build_index(db)
    q_emb = model.encode([query], convert_to_numpy=True)
    D, I = index.search(q_emb, top_k)
    ids = [int(i) for i in I[0] if i != -1]
    if not ids:
        return []
    return db.query(QnaORM).filter(QnaORM.id.in_(ids)).all()
