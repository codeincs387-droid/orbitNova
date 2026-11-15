
import earthaccess

print("Searching NASA collection records...")

collections = earthaccess.search_datasets(
    short_name="M2SMNXEDI"
)

if not collections:
    print("No collections found.")
else:
    for collection in collections:
        info = collection.summary

        print("\n----------------------------")
        print("Short name:", info.get("short-name"))
        print("Version:", collection.version)
        print("Concept ID:", collection.concept_id)
        print("Title:", info.get("entry-title"))
        print("Landing page:", collection.landing_page)
