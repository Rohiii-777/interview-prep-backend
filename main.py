from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db
from routers import categories, qnas,ai, bulk

app = FastAPI(title="QnA Backend - FastAPI",debug=True)

# Allow CORS for frontend
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

# Routers
app.include_router(categories.router)
app.include_router(qnas.router)
app.include_router(ai.router)
app.include_router(bulk.router)

@app.get("/")
def root():
    return {"msg": "QnA backend up. Open /docs for API docs."}
