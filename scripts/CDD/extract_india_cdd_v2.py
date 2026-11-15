
import xarray as xr
from pathlib import Path

input_file = Path(
    "data/raw/merra2/cdd_v2_test/"
    "MERRA2.statM_2d_edi_Nx.v2_1.202001.nc4"
)

output_dir = Path("data/processed/monthly_grid/cdd")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "CDD_India_202001.nc"

print("Opening NASA MERRA-2 CDD V2...")

with xr.open_dataset(input_file) as ds:
    # Extract India bounding box
    india = ds.sel(
        lat=slice(5, 38),
        lon=slice(67, 99)
    )

    # Keep only CDD
    india_cdd = india[["CDD"]]

    # Save extracted data
    india_cdd.to_netcdf(output_file)

    print("\nExtraction successful!")
    print(india_cdd)
    print("\nCDD units:", india_cdd["CDD"].attrs.get("units"))
    print("Output:", output_file)

print("\nDone!")
