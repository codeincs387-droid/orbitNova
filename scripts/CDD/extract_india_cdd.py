
import xarray as xr
from pathlib import Path

input_file = Path(
    "data/raw/merra2/cdd/MERRA2.statM_2d_edi_Nx.202001.nc4"
)

output_dir = Path("data/processed/monthly_grid")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "CDD_India_202001.nc"

# Open source NetCDF
ds = xr.open_dataset(input_file)

# India bounding box
india = ds.sel(
    lat=slice(5, 38),
    lon=slice(67, 99)
)

# Keep only the CDD variable
india_cdd = india[["CDD"]]

# Save extracted dataset
india_cdd.to_netcdf(output_file)

print("India extraction completed!")
print(india_cdd)
print(f"\nSaved to: {output_file}")

ds.close()
