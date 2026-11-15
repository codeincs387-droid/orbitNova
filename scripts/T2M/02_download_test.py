import earthaccess
from pathlib import Path

SHORT_NAME = "M2TMNXSLV"
TEST_VERSION = "5.12.4"

RAW_DIR = Path("data/raw/merra2/temperature")
RAW_DIR.mkdir(parents=True, exist_ok=True)

print("Logging in to NASA Earthdata...")
earthaccess.login()

print("Searching for January 2020 temperature data...")

results = earthaccess.search_data(
short_name=SHORT_NAME,
version=TEST_VERSION,
temporal=("2020-01-01", "2020-01-31"),
count=10
)

if not results:
    raise RuntimeError(
"No files found. Check the collection version and Earthdata access."
)

print("Granules found:", len(results))

downloaded = earthaccess.download(
results,
local_path=str(RAW_DIR)
)

print("\nDownloaded files:")
for item in downloaded:
    print(item)

print("\nTest download completed.")