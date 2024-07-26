from sqlalchemy import Column, Integer, String, DateTime, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    rubrics = Column(ARRAY(String))
    text = Column(String)
    created_date = Column(DateTime, default=datetime.utcnow)
