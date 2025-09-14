from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./db.sqlite"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    _init_fts()

def _init_fts():
    with engine.connect() as conn:
        # Create FTS5 virtual table
        conn.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS qnas_fts
        USING fts5(question, answer, content='qnas', content_rowid='id');
        """))

        # Rebuild index once
        conn.execute(text("INSERT INTO qnas_fts(qnas_fts) VALUES('rebuild')"))

        # Sync triggers
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS qnas_ai AFTER INSERT ON qnas BEGIN
            INSERT INTO qnas_fts(rowid, question, answer)
            VALUES (new.id, new.question, new.answer);
        END;
        """))

        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS qnas_ad AFTER DELETE ON qnas BEGIN
            INSERT INTO qnas_fts(qnas_fts, rowid, question, answer)
            VALUES('delete', old.id, old.question, old.answer);
        END;
        """))

        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS qnas_au AFTER UPDATE ON qnas BEGIN
            INSERT INTO qnas_fts(qnas_fts, rowid, question, answer)
            VALUES('delete', old.id, old.question, old.answer);
            INSERT INTO qnas_fts(rowid, question, answer)
            VALUES (new.id, new.question, new.answer);
        END;
        """))
