import requests


url = "https://api.tfl.gov.uk/Mode/ActiveServiceTypes"

response = requests.get(url, timeout=30)

print("Status code:", response.status_code)

response.raise_for_status()

data = response.json()

print("\nTfL active service types:")
print(data)