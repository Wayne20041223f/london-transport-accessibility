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

# Create an 800 m buffer around each LSOA centroid
lsoa_centroids["buffer_800m"] = lsoa_centroids.geometry.buffer(800)

print("\nFirst 5 centroid buffers:")
print(
    lsoa_centroids[
        ["LSOA21CD", "LSOA21NM", "buffer_800m"]
    ].head()
)

# Visual check of the 800 m centroid buffers
buffer_800m = lsoa_centroids.set_geometry("buffer_800m").copy()

fig, ax = plt.subplots(figsize=(10, 10))

lsoas.boundary.plot(
    ax=ax,
    linewidth=0.2,
    alpha=0.4
)

buffer_800m.iloc[:5].boundary.plot(
    ax=ax,
    linewidth=1.5
)

lsoa_centroids.iloc[:5].plot(
    ax=ax,
    markersize=20
)

ax.set_title("First 5 LSOA Centroids with 800 m Buffers")
ax.set_axis_off()

plt.tight_layout()
plt.show()

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

# Check how many Tube stations fall inside the first buffer
first_buffer = buffer_800m.iloc[[0]].copy()
first_buffer = first_buffer.set_geometry("geometry")

stations_in_first_buffer = gpd.sjoin(
    tube_stations,
    first_buffer[["LSOA21CD", "geometry"]],
    how="inner",
    predicate="within"
)

print("\nTube stations within 800 m of the first LSOA centroid:")
print(stations_in_first_buffer[["stop_id", "name", "LSOA21CD"]])
print("Station count:", len(stations_in_first_buffer))

# Use all 800 m buffers as the active geometry
all_buffers = buffer_800m.copy()
all_buffers = all_buffers.set_geometry("buffer_800m")

# Match Tube stations to all LSOA 800 m buffers
stations_in_buffers = gpd.sjoin(
    tube_stations,
    all_buffers[["LSOA21CD", "buffer_800m"]].rename(
        columns={"buffer_800m": "geometry"}
    ).set_geometry("geometry"),
    how="inner",
    predicate="within"
)

print("\nFirst 10 station-buffer matches:")
print(
    stations_in_buffers[
        ["stop_id", "name", "LSOA21CD"]
    ].head(10)
)

print("\nTotal station-buffer matches:", len(stations_in_buffers))
print(
    "Number of LSOAs with at least one Tube station within 800 m:",
    stations_in_buffers["LSOA21CD"].nunique()
)

# Count Tube stations within 800 m for each LSOA
tube_counts = (
    stations_in_buffers
    .groupby("LSOA21CD")
    .size()
    .reset_index(name="tube_count_800m")
)

print("\nFirst 10 Tube station counts:")
print(tube_counts.head(10))

print("\nNumber of LSOAs currently in tube_counts:", len(tube_counts))

# Add Tube station counts back to all LSOAs
lsoa_access = lsoa_access.merge(
    tube_counts,
    on="LSOA21CD",
    how="left"
)

# LSOAs with no Tube station within 800 m currently have NaN.
# Replace these missing values with 0.
lsoa_access["tube_count_800m"] = (
    lsoa_access["tube_count_800m"]
    .fillna(0)
    .astype(int)
)

print("\nFirst 10 final accessibility results:")
#print(
#    lsoa_access[
#        ["LSOA21CD", "distance_to_tube_m_", "tube_count_800m"]
#    ].head(10)
#)
print("\nColumns currently in lsoa_access:")
print(lsoa_access.columns.tolist())

print("\nNumber of final LSOA rows:", len(lsoa_access))
print(
    "LSOAs with zero Tube stations within 800 m:",
    (lsoa_access["tube_count_800m"] == 0).sum()
)

# Load the previously saved nearest-Tube accessibility results
distance_results = gpd.read_file(
    processed_folder / "lsoa_tube_accessibility.gpkg"
)

# Add the new 800 m Tube station count to the existing distance results
final_accessibility = distance_results.merge(
    lsoa_access[["LSOA21CD", "tube_count_800m"]],
    on="LSOA21CD",
    how="left"
)

print("\nFinal accessibility dataset:")
print(
    final_accessibility[
        [
            "LSOA21CD",
            "nearest_tube_name",
            "distance_to_tube_m",
            "tube_count_800m"
        ]
    ].head(10)
)

print("\nNumber of rows:", len(final_accessibility))