from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from db import Base

class CategoryORM(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    qnas = relationship("QnaORM", back_populates="category", cascade="delete")

class QnaORM(Base):
    __tablename__ = "qnas"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=True, index=True)
    is_done = Column(Boolean, default=False, index=True)
    bookmark = Column(Boolean, default=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    category = relationship("CategoryORM", back_populates="qnas")
