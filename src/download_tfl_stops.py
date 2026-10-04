from pathlib import Path
import os

import requests
from dotenv import load_dotenv


# Locate the project root and load environment variables
project_root = Path(__file__).resolve().parent.parent
env_file = project_root / ".env"

load_dotenv(env_file)

# Read the TfL API key without exposing it in the code
api_key = os.getenv("TFL_API_KEY")

assert api_key, "TFL_API_KEY was not found in .env"

# Make a small test request to the TfL StopPoint API
url = "https://api.tfl.gov.uk/StopPoint/Mode/tube"

params = {
    "app_key": api_key
}

response = requests.get(url, params=params, timeout=30)

print("Status code:", response.status_code)

response.raise_for_status()

data = response.json()

stop_points = data.get("stopPoints", [])

print("Number of Tube StopPoints:", len(stop_points))

print("\nFirst 5 StopPoints:")

for stop in stop_points[:5]:
    print(
        stop.get("commonName"),
        "|",
        stop.get("stopType"),
        "|",
        stop.get("naptanId")
    )

stop_types = {}

for stop in stop_points:
    stop_type = stop.get("stopType")

    if stop_type not in stop_types:
        stop_types[stop_type] = 0

    stop_types[stop_type] += 1


print("\nStop types:")

for stop_type, count in stop_types.items():
    print(stop_type, ":", count)

print("\nExamples of TransportInterchange:")

interchanges = [
    stop
    for stop in stop_points
    if stop.get("stopType") == "TransportInterchange"
]

for stop in interchanges[:15]:
    print(
        stop.get("commonName"),
        "|",
        stop.get("naptanId"),
        "|",
        stop.get("modes")
    )
