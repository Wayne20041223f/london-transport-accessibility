from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt


# Locate project folders
project_root = Path(__file__).resolve().parent.parent
processed_folder = project_root / "data" / "processed"


# Load spatial datasets
lsoas = gpd.read_file(
    processed_folder / "london_lsoas_2021.gpkg"
)

tube_stations = gpd.read_file(
    processed_folder / "tube_stations.gpkg"
)


# Basic checks
print("Number of LSOAs:", len(lsoas))
print("Number of Tube station records:", len(tube_stations))

print("LSOA CRS:", lsoas.crs)
print("Tube CRS:", tube_stations.crs)

assert lsoas.crs == tube_stations.crs
assert lsoas.crs.to_epsg() == 27700

# Create a copy for accessibility analysis
lsoa_access = lsoas.copy()

# Calculate the geometric centroid of each LSOA
lsoa_access["centroid"] = lsoa_access.geometry.centroid

print("\nFirst 5 LSOA centroids:")
print(
    lsoa_access[
        ["LSOA21CD", "LSOA21NM", "centroid"]
    ].head()
)

# Use the LSOA centroids as the active geometry
lsoa_centroids = lsoa_access.set_geometry("centroid").copy()

print("\nActive geometry:", lsoa_centroids.geometry.name)
print("CRS:", lsoa_centroids.crs)
print("Number of centroids:", len(lsoa_centroids))

# Prepare Tube station columns for the nearest-neighbour join
tube_for_join = tube_stations[
    ["stop_id", "name", "geometry"]
].copy()

tube_for_join = tube_for_join.rename(
    columns={
        "stop_id": "nearest_tube_id",
        "name": "nearest_tube_name"
    }
)


# Find the nearest Tube station to each LSOA centroid
nearest_tube = gpd.sjoin_nearest(
    lsoa_centroids,
    tube_for_join,
    how="left",
    distance_col="distance_to_tube_m"
)

print("\nNearest Tube results:")
print(
    nearest_tube[
        [
            "LSOA21CD",
            "LSOA21NM",
            "nearest_tube_name",
            "distance_to_tube_m"
        ]
    ].head(10)
)

print("\nNumber of result rows:", len(nearest_tube))

# Summarise the Tube accessibility indicator
distance_summary = nearest_tube["distance_to_tube_m"].describe()

print("\nDistance to nearest Tube station (metres):")
print(distance_summary)

# Restore the LSOA polygons as the active geometry
access_map = nearest_tube.set_geometry("geometry").copy()

# Plot Tube accessibility
fig, ax = plt.subplots(figsize=(10, 10))

access_map.plot(
    column="distance_to_tube_m",
    ax=ax,
    legend=True,
    scheme="quantiles",
    k=5,
    edgecolor="none"
)

tube_stations.plot(
    ax=ax,
    markersize=5
)

ax.set_title(
    "Distance from LSOA Centroid to Nearest Tube Station"
)
ax.set_axis_off()

plt.tight_layout()

figure_folder = project_root / "outputs" / "figures"
figure_folder.mkdir(parents=True, exist_ok=True)

figure_file = figure_folder / "tube_accessibility_distance.png"

plt.savefig(
    figure_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nSaved map to: {figure_file}")

plt.show()

# Save LSOA accessibility results
output_file = processed_folder / "lsoa_tube_accessibility.gpkg"

# Remove extra geometry columns before saving
columns_to_drop = [
    col for col in access_map.columns
    if col != access_map.geometry.name
    and str(access_map[col].dtype) == "geometry"
]

access_map = access_map.drop(columns=columns_to_drop)

access_map.to_file(
    output_file,
    driver="GPKG"
)

print(f"\nSaved accessibility results to: {output_file}")