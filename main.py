from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Document
from dotenv import load_dotenv
import os
import requests

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DocumentCreate(BaseModel):
    rubrics: List[str]
    text: str


class DocumentRead(BaseModel):
    id: int
    rubrics: List[str]
    text: str
    created_date: str


@app.post("/documents/", response_model=DocumentRead)
def create_document(doc: DocumentCreate, db: Session = Depends(get_db)):
    new_doc = Document(rubrics=doc.rubrics, text=doc.text)
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    url = f"http://elasticsearch:9200/documents/_doc/{new_doc.id}"
    headers = {"Content-Type": "application/json"}
    data = {
        "text": new_doc.text,
        "created_date": new_doc.created_date.isoformat()
    }
    response = requests.put(url, json=data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"Failed to index document {new_doc.id}: {response.status_code}, {response.text}")

    return DocumentRead(
        id=new_doc.id,
        rubrics=new_doc.rubrics,
        text=new_doc.text,
        created_date=new_doc.created_date.isoformat()
    )


@app.get("/documents/{doc_id}", response_model=DocumentRead)
def read_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentRead(
        id=doc.id,
        rubrics=doc.rubrics,
        text=doc.text,
        created_date=doc.created_date.isoformat()  # Преобразование в строку
    )


@app.get("/search", response_model=List[DocumentRead])
def search_documents(query: str = Query(..., description="Search query")):
    url = "http://elasticsearch:9200/documents/_search"
    headers = {"Content-Type": "application/json"}
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["text"]
            }
        },
        "size": 20,  # Возвращать первые 20 результатов
        "sort": [{"created_date": "desc"}]  # Упорядочивание по дате создания
    }
    response = requests.post(url, json=search_body, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    hits = response.json()['hits']['hits']
    result = []
    for hit in hits:
        doc_id = hit['_id']
        url = f"http://elasticsearch:9200/documents/_doc/{doc_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            doc = response.json()["_source"]
            result.append(DocumentRead(
                id=doc_id,
                rubrics=doc.get('rubrics', []),
                text=doc.get('text', ''),
                created_date=doc.get('created_date', '')
            ))
    return result


@app.get("/elasticsearch/documents/{doc_id}", response_model=DocumentRead)
def get_document_from_elasticsearch(doc_id: int):
    url = f"http://elasticsearch:9200/documents/_doc/{doc_id}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    doc = response.json()["_source"]
    return DocumentRead(
        id=doc_id,
        rubrics=doc.get('rubrics', []),
        text=doc["text"],
        created_date=doc.get('created_date', '')
    )


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()

    url = f"http://elasticsearch:9200/documents/_doc/{doc_id}"
    headers = {"Content-Type": "application/json"}
    response = requests.delete(url, headers=headers)
    if response.status_code not in [200, 202]:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"message": "Document deleted successfully"}
