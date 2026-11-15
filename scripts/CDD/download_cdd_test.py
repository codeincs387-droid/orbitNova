
import earthaccess
from pathlib import Path

# Keep V2 test data separate from the earlier download
output_dir = Path("data/raw/merra2/cdd_v2_test")
output_dir.mkdir(parents=True, exist_ok=True)

india_bbox = (67, 5, 99, 38)

print("Logging in to NASA Earthdata...")
earthaccess.login()

print("Searching MERRA-2 CDD Version 2...")

results = earthaccess.search_data(
    short_name="M2SMNXEDI",
    version="2",
    bounding_box=india_bbox,
    temporal=("2020-01-01", "2020-12-31"),
    count=1
)

if not results:
    print("No V2 granules found.")
else:
    print(f"Found {len(results)} granule(s).")

    downloaded = earthaccess.download(
        results,
        local_path=str(output_dir)
    )

    print("\nDownloaded V2 test file:")
    for file in downloaded:
        print(file)
