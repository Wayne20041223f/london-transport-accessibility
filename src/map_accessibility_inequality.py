from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt


# Project folders
project_root = Path(__file__).resolve().parents[1]
processed_folder = project_root / "data" / "processed"

# Load the final analysis dataset
analysis_file = (
    processed_folder
    / "london_accessibility_inequality.gpkg"
)

analysis = gpd.read_file(analysis_file)

print("Number of LSOAs:", len(analysis))
print("Priority LSOAs:", analysis["priority_area"].sum())
print("CRS:", analysis.crs)

# Select priority LSOAs
priority = analysis[analysis["priority_area"]].copy()

# Create map
fig, ax = plt.subplots(figsize=(10, 10))

# Plot all London LSOAs as background
analysis.plot(
    ax=ax,
    color="lightgrey",
    edgecolor="white",
    linewidth=0.1
)

# Highlight priority LSOAs
priority.plot(
    ax=ax,
    color="crimson",
    edgecolor="none"
)

ax.set_title(
    "Higher Deprivation and Poorer Tube Accessibility in London\n"
    "IMD Deciles 1–3 and >2 km from Nearest Tube Station"
)

ax.set_axis_off()

plt.tight_layout()

# Save map
map_file = (
    project_root
    / "outputs"
    / "maps"
    / "priority_accessibility_inequality.png"
)

fig.savefig(
    map_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"\nSaved map to: {map_file}")

plt.show()