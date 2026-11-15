
import earthaccess

SHORT_NAME = "M2TMNXSLV"

print("Searching NASA Earthdata collections...")

collections = earthaccess.search_datasets(
    short_name=SHORT_NAME
)

if not collections:
    raise RuntimeError(
        "MERRA-2 temperature collection not found."
    )

for i, collection in enumerate(collections, start=1):

    print(f"\nCollection {i}")

    metadata = collection.render_dict
    umm = metadata.get("umm", {})

    print("Short name:", umm.get("ShortName"))
    print("Version:", collection.version)
    print("Concept ID:", collection.concept_id)
    print("Title:", umm.get("EntryTitle"))

    print("\nAbstract:")
    print(collection.abstract)

    print("\nSummary:")
    print(collection.summary)

print("\nCollection inspection completed successfully.")

