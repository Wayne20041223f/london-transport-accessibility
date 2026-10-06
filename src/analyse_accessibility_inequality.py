from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

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

# Calculate median Tube distance for each IMD decile
median_distance_by_decile = (
    analysis
    .groupby("imd_decile")["distance_to_tube_m"]
    .median()
)

# Plot median distance by IMD decile
fig, ax = plt.subplots(figsize=(8, 5))

median_distance_by_decile.plot(
    kind="bar",
    ax=ax
)

ax.set_title(
    "Median Distance to Nearest Tube Station by IMD Decile"
)
ax.set_xlabel(
    "IMD Decile (1 = Most Deprived, 10 = Least Deprived)"
)
ax.set_ylabel(
    "Median Distance to Nearest Tube Station (m)"
)

plt.tight_layout()

figure_file = (
    project_root
    / "outputs"
    / "figures"
    / "median_tube_distance_by_imd_decile.png"
)

fig.savefig(
    figure_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nSaved figure to: {figure_file}")

plt.show()

# Compare the distribution of Tube distance across IMD deciles
fig, ax = plt.subplots(figsize=(10, 6))

analysis.boxplot(
    column="distance_to_tube_m",
    by="imd_decile",
    ax=ax,
    showfliers=False
)

ax.set_title(
    "Distance to Nearest Tube Station by IMD Decile"
)
ax.set_xlabel(
    "IMD Decile (1 = Most Deprived, 10 = Least Deprived)"
)
ax.set_ylabel(
    "Distance to Nearest Tube Station (m)"
)

# Remove pandas' automatic extra title
plt.suptitle("")

plt.tight_layout()

figure_file = (
    project_root
    / "outputs"
    / "figures"
    / "tube_distance_distribution_by_imd_decile.png"
)

fig.savefig(
    figure_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nSaved figure to: {figure_file}")

plt.show()

# Identify LSOAs with both higher deprivation
# and poorer Tube accessibility
analysis["high_deprivation"] = (
    analysis["imd_decile"] <= 3
)

analysis["poor_tube_access"] = (
    analysis["distance_to_tube_m"] > 2000
)

analysis["priority_area"] = (
    analysis["high_deprivation"]
    & analysis["poor_tube_access"]
)

# Save the complete analysis dataset
analysis_file = (
    processed_folder
    / "london_accessibility_inequality.gpkg"
)

analysis.to_file(
    analysis_file,
    driver="GPKG"
)

print(f"\nSaved analysis dataset to: {analysis_file}")

print("\nCombined accessibility-deprivation classification:")
print(
    analysis[
        ["high_deprivation", "poor_tube_access", "priority_area"]
    ].sum()
)

print(
    "\nPercentage of London LSOAs classified as priority areas:"
)
print(
    round(
        analysis["priority_area"].mean() * 100,
        1
    )
)

# Count priority LSOAs by local authority
priority_by_lad = (
    analysis[analysis["priority_area"]]
    .groupby("LAD23NM")
    .size()
    .sort_values(ascending=False)
)

print("\nPriority LSOAs by local authority:")
print(priority_by_lad.head(10))

# Calculate the percentage of priority LSOAs within each local authority
lad_summary = (
    analysis.groupby("LAD23NM")
    .agg(
        total_lsoas=("LSOA21CD", "size"),
        priority_lsoas=("priority_area", "sum")
    )
)

lad_summary["priority_percentage"] = (
    lad_summary["priority_lsoas"]
    / lad_summary["total_lsoas"]
    * 100
)

lad_summary = lad_summary.sort_values(
    "priority_percentage",
    ascending=False
)

print("\nPriority LSOA percentage by local authority:")
print(lad_summary.head(10).round(1))

# Plot priority LSOA percentage by local authority
top_lads = lad_summary.head(10).sort_values(
    "priority_percentage",
    ascending=True
)

fig, ax = plt.subplots(figsize=(9, 6))

ax.barh(
    top_lads.index,
    top_lads["priority_percentage"]
)

ax.set_title(
    "London Boroughs with the Highest Share of Priority LSOAs"
)
ax.set_xlabel(
    "Priority LSOAs (% of borough LSOAs)"
)
ax.set_ylabel("Local Authority")

plt.tight_layout()

figure_path = (
    Path(__file__).resolve().parent.parent
    / "outputs"
    / "figures"
    / "priority_lsoa_percentage_by_borough.png"
)

plt.savefig(
    figure_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print(f"\nSaved figure to: {figure_path}")