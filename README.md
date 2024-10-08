### Data stored in data folder

  initial data in posts.csv file

### Starting containers

docker-compose up --build

Indexes are created in the background. Data is imported in the background.

After running `docker-compose up`, wait until fastAPI server is up and running.

### Swagger documentation

http://localhost:8000/docs

### Commands

curl -X 'GET' \
  'http://127.0.0.1:8000/search?query=SEARCH_TEXT' \
  -H 'accept: application/json'

curl -X 'GET' \
  'http://127.0.0.1:8000/documents/DOCUMENT_ID' \
  -H 'accept: application/json'

curl -X 'DELETE' \
  'http://127.0.0.1:8000/documents/DOCUMENT_ID' \
  -H 'accept: application/json'

curl -X 'POST' \
  'http://127.0.0.1:8000/documents/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "rubrics": [
    "YOUR_RUBRICS"
  ],
  "text": "YOUR_POST"
}'

### Tests

docker ps
docker exec -it WEB_CONTAINER_ID pytest
