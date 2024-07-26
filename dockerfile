FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python app/create_index.py && python app/import_data.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
