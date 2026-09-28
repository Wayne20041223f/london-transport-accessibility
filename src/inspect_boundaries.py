from pathlib import Path
import geopandas as gpd

# Locate the project's raw data folder
project_root = Path(__file__).resolve().parent.parent
raw_folder = project_root / "data" / "raw"

# Find the downloaded GeoPackage
gpkg_files = list(raw_folder.glob("*.gpkg"))
assert len(gpkg_files) == 1, "Expected exactly one GeoPackage"

# Read the official LSOA boundaries
lsoas = gpd.read_file(gpkg_files[0])

print("Number of LSOAs:", len(lsoas))
print("Columns:", lsoas.columns.tolist())
print("CRS:", lsoas.crs)
print("\nFirst five rows:")
print(lsoas.head())