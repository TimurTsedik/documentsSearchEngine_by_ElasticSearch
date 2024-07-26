import requests
import time

print("Starting Elasticsearch index creation...")

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

index_name = "documents"
url = f"{es_url}/{index_name}"
headers = {"Content-Type": "application/json"}
index_body = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "text": {"type": "text"},
            "created_date": {"type": "date"}
        }
    }
}

response = requests.put(url, json=index_body, headers=headers)
if response.status_code == 200:
    print(f"Index '{index_name}' created successfully")
elif response.status_code == 400 and "resource_already_exists_exception" in response.text:
    print(f"Index '{index_name}' already exists")
else:
    print(f"Failed to create index: {response.status_code}, {response.text}")

print("Elasticsearch index creation completed.")
