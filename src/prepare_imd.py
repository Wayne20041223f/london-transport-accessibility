from pathlib import Path
import pandas as pd
import geopandas as gpd

# Define project folders
project_root = Path(__file__).resolve().parents[1]
raw_folder = project_root / "data" / "raw"

# Path to the English Indices of Deprivation 2025 file
imd_file = raw_folder / "File_1_IoD2025_Index_of_Multiple_Deprivation.xlsx"

# Read the IMD25 worksheet
imd = pd.read_excel(
    imd_file,
    sheet_name="IMD25"
)

print(imd.head())
print("\nNumber of rows:", len(imd))
print("\nColumns:")
print(imd.columns.tolist())

# Read the prepared Greater London LSOA boundaries
processed_folder = project_root / "data" / "processed"
london_lsoa_file = processed_folder / "london_lsoas_2021.gpkg"

london_lsoas = gpd.read_file(london_lsoa_file)

print("\nNumber of London LSOAs:", len(london_lsoas))
print(
    "London LSOAs found in IMD:",
    london_lsoas["LSOA21CD"].isin(imd["LSOA code (2021)"]).sum()
)

# Keep only the IMD variables needed for V1
imd_selected = imd.iloc[:, [0, 4, 5]].copy()

# Give the three selected columns simple names
imd_selected.columns = [
    "LSOA21CD",
    "imd_rank",
    "imd_decile"
]

print("\nSelected IMD columns:")
print(imd_selected.columns.tolist())

# Merge IMD data with London LSOAs
london_imd = london_lsoas.merge(
    imd_selected,
    on="LSOA21CD",
    how="left"
)

print("\nLondon IMD data:")
print(london_imd[["LSOA21CD", "imd_rank", "imd_decile"]].head())

print("\nNumber of rows after merge:", len(london_imd))
print("\nMissing IMD ranks:", london_imd["imd_rank"].isna().sum())
print("Missing IMD deciles:", london_imd["imd_decile"].isna().sum())

# Save the prepared London IMD dataset
output_file = processed_folder / "london_imd_2025.gpkg"

london_imd.to_file(
    output_file,
    driver="GPKG"
)

print(f"\nSaved London IMD dataset to: {output_file}")