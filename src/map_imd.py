from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt


# Define project folders
project_root = Path(__file__).resolve().parents[1]
processed_folder = project_root / "data" / "processed"

# Read the prepared London IMD dataset
imd_file = processed_folder / "london_imd_2025.gpkg"
london_imd = gpd.read_file(imd_file)

print("Number of LSOAs:", len(london_imd))
print("\nIMD decile counts:")
print(london_imd["imd_decile"].value_counts().sort_index())

# Map IMD deciles
fig, ax = plt.subplots(figsize=(10, 10))

london_imd.plot(
    column="imd_decile",
    cmap="RdYlGn",
    legend=True,
    ax=ax,
    edgecolor="none",
    vmin=1,
    vmax=10
)

ax.set_title(
    "Index of Multiple Deprivation 2025 — London\n"
    "1 = Most Deprived, 10 = Least Deprived"
)
ax.set_axis_off()

plt.tight_layout()
plt.show()