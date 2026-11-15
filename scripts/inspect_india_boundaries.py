
import geopandas as gpd

path = "data/reference/india_states_ut.geojson"

gdf = gpd.read_file(path)

print("========== INDIA BOUNDARY CHECK ==========")
print("Total features:", len(gdf))
print("Geometry types:", gdf.geometry.geom_type.unique())
print("CRS:", gdf.crs)
print("\nAvailable columns:")
print(gdf.columns.tolist())

print("\nFirst five records:")
print(gdf.head())

print("\nMissing geometries:", gdf.geometry.isna().sum())
print("Invalid geometries:", (~gdf.geometry.is_valid).sum())
