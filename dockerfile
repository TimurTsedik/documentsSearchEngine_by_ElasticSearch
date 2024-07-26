FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python create_index.py && python import_data.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
