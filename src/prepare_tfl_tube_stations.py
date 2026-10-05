from pathlib import Path
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
from dotenv import load_dotenv


# Locate the project root
project_root = Path(__file__).resolve().parent.parent

# Load the TfL API key from .env
load_dotenv(project_root / ".env")

api_key = os.getenv("TFL_API_KEY")

assert api_key, "TFL_API_KEY was not found in .env"


# Request all Tube StopPoints from the TfL API
url = "https://api.tfl.gov.uk/StopPoint/Mode/tube"

params = {
    "app_key": api_key
}

response = requests.get(url, params=params, timeout=30)

print("Status code:", response.status_code)

response.raise_for_status()

data = response.json()

stop_points = data.get("stopPoints", [])

print("Number of raw Tube StopPoints:", len(stop_points))

# Keep only station-level StopPoints
station_types = {
    "NaptanMetroStation",
    "TransportInterchange",
}

station_points = [
    stop
    for stop in stop_points
    if stop.get("stopType") in station_types
]

print("Number of station-level StopPoints:", len(station_points))

# Convert station-level StopPoints into a table
station_records = []

for stop in station_points:
    station_records.append({
        "stop_id": stop.get("naptanId"),
        "name": stop.get("commonName"),
        "stop_type": stop.get("stopType"),
        "modes": stop.get("modes"),
        "lat": stop.get("lat"),
        "lon": stop.get("lon"),
    })

stations_df = pd.DataFrame(station_records)

print("\nStation table:")
print(stations_df.head())

print("\nTable shape:", stations_df.shape)
print("\nColumns:", stations_df.columns.tolist())

# Check for duplicate StopPoint IDs
duplicate_ids = stations_df["stop_id"].duplicated().sum()

print("\nDuplicate stop IDs:", duplicate_ids)
print("Unique stop IDs:", stations_df["stop_id"].nunique())

# Check for repeated station names
duplicate_names = stations_df[
    stations_df["name"].duplicated(keep=False)
].sort_values("name")

print("\nRows with repeated station names:")
print(duplicate_names[[
    "stop_id",
    "name",
    "stop_type",
    "modes",
    "lat",
    "lon"
]].to_string(index=False))

print("\nNumber of unique station names:", stations_df["name"].nunique())

# Convert the pandas DataFrame to a GeoDataFrame
stations_gdf = gpd.GeoDataFrame(
    stations_df,
    geometry=gpd.points_from_xy(
        stations_df["lon"],
        stations_df["lat"]
    ),
    crs="EPSG:4326"
)

print("\nOriginal CRS:", stations_gdf.crs)

# Reproject to British National Grid
stations_gdf = stations_gdf.to_crs("EPSG:27700")

print("Projected CRS:", stations_gdf.crs)

print("\nFirst 5 geometries:")
print(stations_gdf[["name", "geometry"]].head())

# Load the prepared London LSOA boundaries
lsoa_file = project_root / "data" / "processed" / "london_lsoas_2021.gpkg"

london_lsoas = gpd.read_file(lsoa_file)

print("\nLSOA CRS:", london_lsoas.crs)
print("Tube CRS:", stations_gdf.crs)

assert london_lsoas.crs == stations_gdf.crs, "CRS mismatch"


# Plot LSOAs and Tube stations together
fig, ax = plt.subplots(figsize=(10, 10))

london_lsoas.plot(
    ax=ax,
    facecolor="lightgrey",
    edgecolor="white",
    linewidth=0.2
)

stations_gdf.plot(
    ax=ax,
    markersize=8
)

ax.set_title("Candidate Tube Station Points and London LSOAs")
ax.set_axis_off()

plt.tight_layout()
plt.show()

# Create a single Greater London boundary
london_boundary = london_lsoas.geometry.union_all()

# Check which station points fall within Greater London
inside_london = stations_gdf.geometry.within(london_boundary)

print("\nStations inside Greater London:", inside_london.sum())
print("Stations outside Greater London:", (~inside_london).sum())

# Inspect station points outside Greater London
outside_stations = stations_gdf.loc[
    ~inside_london,
    ["stop_id", "name", "stop_type", "modes", "geometry"]
]

print("\nStations outside Greater London:")
print(
    outside_stations
    .sort_values("name")
    .to_string(index=False)
)

# Keep only station-level points within Greater London
london_tube_stations = stations_gdf.loc[inside_london].copy()

print("\nFinal Greater London Tube records:", len(london_tube_stations))

assert len(london_tube_stations) == 320
assert london_tube_stations.crs.to_epsg() == 27700

# Final quality checks
print("\nStop type counts:")
print(london_tube_stations["stop_type"].value_counts())

all_have_tube = london_tube_stations["modes"].apply(
    lambda modes: "tube" in modes
).all()

print("\nAll records include tube mode:", all_have_tube)

missing_coordinates = london_tube_stations[
    ["lat", "lon"]
].isna().any(axis=1).sum()

print("Records with missing coordinates:", missing_coordinates)

# Save the cleaned Greater London Tube station dataset
processed_folder = project_root / "data" / "processed"
output_file = processed_folder / "tube_stations.gpkg"

london_tube_stations.to_file(
    output_file,
    driver="GPKG"
)

print(f"\nSaved Tube stations to: {output_file}")
