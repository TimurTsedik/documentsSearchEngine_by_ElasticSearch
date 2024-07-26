import requests
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Document
from dotenv import load_dotenv
import os
import time

print("Starting data import...")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

es_url = "http://elasticsearch:9200"
max_retries = 12
retries = 0
while retries < max_retries:
    try:
        response = requests.get(es_url)
        if response.status_code == 200:
            print("Connected to Elasticsearch")
            break
    except requests.exceptions.RequestException as e:
        print(f"Waiting for Elasticsearch... ({retries}/{max_retries}) Error: {e}")
        retries += 1
        time.sleep(10)

if retries == max_retries:
    print("Failed to connect to Elasticsearch after multiple attempts.")
    exit(1)

Base.metadata.create_all(bind=engine)


def import_data(csv_file):
    session = SessionLocal()
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rubrics = []
            text = row['text']

            new_doc = Document(rubrics=rubrics, text=text)
            session.add(new_doc)
            session.commit()
            session.refresh(new_doc)

            url = f"{es_url}/documents/_doc/{new_doc.id}"
            headers = {"Content-Type": "application/json"}
            data = {
                "text": text,
                "created_date": new_doc.created_date.isoformat()
            }
            response = requests.put(url, json=data, headers=headers)
            if response.status_code not in [200, 201]:
                print(f"Failed to index document {new_doc.id}: {response.status_code}, {response.text}")

    session.close()


if __name__ == "__main__":
    import_data('data/posts.csv')
    print("Data import completed.")
