from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

# Find the project folder
project_root = Path(__file__).resolve().parent.parent

# Path to the Tube accessibility dataset
accessibility_file = (
    project_root
    / "data"
    / "processed"
    / "lsoa_tube_accessibility.gpkg"
)

# Read the dataset
lsoa_access = gpd.read_file(accessibility_file)

print("Number of LSOAs:", len(lsoa_access))
print("CRS:", lsoa_access.crs)
print("Columns:", lsoa_access.columns.tolist())

print("\nFirst 5 rows:")
print(
    lsoa_access[
        [
            "LSOA21CD",
            "LSOA21NM",
            "nearest_tube_name",
            "distance_to_tube_m",
            "tube_count_800m",
        ]
    ].head()
)

# Map distance to the nearest Tube station
fig, ax = plt.subplots(figsize=(10, 10))

lsoa_access.plot(
    column="distance_to_tube_m",
    ax=ax,
    legend=True,
    edgecolor="none"
)

ax.set_title("Distance to Nearest Tube Station")
ax.set_axis_off()

plt.tight_layout()
plt.show()
print("\nDistance to nearest Tube station summary:")
print(lsoa_access["distance_to_tube_m"].describe())
fig, ax = plt.subplots(figsize=(8, 5))

lsoa_access["distance_to_tube_m"].plot(
    kind="hist",
    bins=40,
    ax=ax
)

ax.set_title("Distribution of Distance to Nearest Tube Station")
ax.set_xlabel("Distance to nearest Tube station (m)")
ax.set_ylabel("Number of LSOAs")

plt.tight_layout()
plt.show()

# Create a quantile map of distance to nearest Tube station
fig, ax = plt.subplots(figsize=(10, 10))

lsoa_access.plot(
    column="distance_to_tube_m",
    scheme="quantiles",
    k=5,
    legend=True,
    ax=ax
)

ax.set_title("Distance to Nearest Tube Station (Quintiles)")
ax.set_axis_off()

plt.tight_layout()
plt.show()