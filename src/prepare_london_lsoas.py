from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Locate the project's raw data folder
project_root = Path(__file__).resolve().parent.parent
raw_folder = project_root / "data" / "raw"

# Find the LSOA-to-LAD lookup CSV
csv_files = list(raw_folder.glob("*.csv"))
assert len(csv_files) == 1, "Expected exactly one CSV file"

# Read the lookup table
lookup = pd.read_csv(csv_files[0])

# Inspect the data
print("Number of rows:", len(lookup))
print("Columns:", lookup.columns.tolist())

print("\nFirst five rows:")
print(lookup.head())
# Inspect local authorities containing "London"
london_names = lookup[
    lookup["LAD23NM"].str.contains("London", case=False, na=False)
]["LAD23NM"].unique()

print("\nLocal authorities containing 'London':")
print(london_names)
# Select LSOAs belonging to Greater London
london_lookup = lookup[
    lookup["LAD23CD"].str.startswith("E09", na=False)
].copy()

print("\nNumber of London LSOAs:", len(london_lookup))
print("Number of London local authorities:", london_lookup["LAD23CD"].nunique())

print("\nLondon local authorities:")
print(sorted(london_lookup["LAD23NM"].unique()))

# Find and read the LSOA boundary GeoPackage
gpkg_files = list(raw_folder.glob("*.gpkg"))
assert len(gpkg_files) == 1, "Expected exactly one GeoPackage"

boundaries = gpd.read_file(gpkg_files[0])

# Merge London lookup information with LSOA boundaries
london_lsoas = boundaries.merge(
    london_lookup[["LSOA21CD", "LAD23CD", "LAD23NM"]],
    on="LSOA21CD",
    how="inner"
)

# Validate the merged GeoDataFrame
print("\nMerged London GeoDataFrame:")
print("Number of rows:", len(london_lsoas))
print("Number of local authorities:", london_lsoas["LAD23CD"].nunique())
print("CRS:", london_lsoas.crs)
print("Geometry column:", london_lsoas.geometry.name)

# Plot the London LSOA boundaries
fig, ax = plt.subplots(figsize=(10, 10))

london_lsoas.plot(
    ax=ax,
    edgecolor="black",
    facecolor="lightgrey",
    linewidth=0.2
)

ax.set_title("Greater London 2021 LSOA Boundaries")
ax.set_axis_off()

plt.tight_layout()
plt.show()

# Save the prepared London LSOA dataset
processed_folder = project_root / "data" / "processed"
output_file = processed_folder / "london_lsoas_2021.gpkg"

london_lsoas.to_file(output_file, driver="GPKG")

print(f"\nSaved processed London LSOAs to: {output_file}")