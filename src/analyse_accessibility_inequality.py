from pathlib import Path
import geopandas as gpd


# Define project folders
project_root = Path(__file__).resolve().parents[1]
processed_folder = project_root / "data" / "processed"

# Read Tube accessibility data
accessibility = gpd.read_file(
    processed_folder / "lsoa_tube_accessibility.gpkg"
)

# Read IMD data
imd = gpd.read_file(
    processed_folder / "london_imd_2025.gpkg"
)

print("Accessibility rows:", len(accessibility))
print("IMD rows:", len(imd))

print("\nAccessibility columns:")
print(accessibility.columns.tolist())

print("\nIMD columns:")
print(imd.columns.tolist())

# Keep only the IMD variables needed for the analysis
imd_variables = imd[
    ["LSOA21CD", "imd_rank", "imd_decile"]
].copy()

# Merge IMD variables into the Tube accessibility dataset
analysis = accessibility.merge(
    imd_variables,
    on="LSOA21CD",
    how="left"
)

# Check the merged dataset
print("\nMerged analysis dataset:")
print(
    analysis[
        [
            "LSOA21CD",
            "distance_to_tube_m",
            "tube_count_800m",
            "imd_rank",
            "imd_decile"
        ]
    ].head()
)

print("\nNumber of rows after merge:", len(analysis))
print("Missing Tube distances:", analysis["distance_to_tube_m"].isna().sum())
print("Missing Tube counts:", analysis["tube_count_800m"].isna().sum())
print("Missing IMD ranks:", analysis["imd_rank"].isna().sum())
print("Missing IMD deciles:", analysis["imd_decile"].isna().sum())

# Compare Tube accessibility across IMD deciles
distance_by_decile = (
    analysis
    .groupby("imd_decile")["distance_to_tube_m"]
    .agg(["count", "mean", "median"])
)

print("\nDistance to nearest Tube station by IMD decile:")
print(distance_by_decile.round(1))

# Compare nearby Tube station counts across IMD deciles
count_by_decile = (
    analysis
    .groupby("imd_decile")["tube_count_800m"]
    .agg(["count", "mean", "median"])
)

print("\nTube stations within 800 m by IMD decile:")
print(count_by_decile.round(2))

# Spearman correlations between deprivation and Tube accessibility
distance_corr = analysis[
    ["imd_rank", "distance_to_tube_m"]
].corr(method="spearman").iloc[0, 1]

count_corr = analysis[
    ["imd_rank", "tube_count_800m"]
].corr(method="spearman").iloc[0, 1]

print("\nSpearman correlations:")
print(
    "IMD rank vs distance to nearest Tube:",
    round(distance_corr, 3)
)
print(
    "IMD rank vs Tube count within 800 m:",
    round(count_corr, 3)
)