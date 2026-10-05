
from datetime import  datetime, timezone
import json 
from pathlib import Path 

import csv
project_folder =Path(__file__).resolve().parent

raw_folder = project_folder / "data" / "raw" / "2026-10-01_sample"

releases = []

for raw_file in sorted(raw_folder.glob("page_*.json")):
    raw_text = raw_file.read_text(encoding="utf-8")
    data = json.loads(raw_text)
    releases.extend(data["releases"])


first_release = releases[0]
print(first_release["tender"]["title"])

print("Number of notices:", len(releases))
print("Notice type:", first_release["tag"])
print("Tender status:", first_release["tender"]["status"]) 

# Fixed reference time for the first draft: 5 October 2026, 11:00 UTC.
now = datetime(2026, 10, 5, 11, 0, tzinfo=timezone.utc)

rows = []


for release in releases:

    tender = release.get("tender") or {}
    buyer = release.get("buyer") or {}
    value = tender.get("value") or {}
    tender_period = tender.get("tenderPeriod") or {}
    classification = tender.get("classification") or {}
    row = {
        "release_id": release.get("id"),
        "ocid": release.get("ocid"),
        "title": tender.get("title"),
        "buyer_name": buyer.get("name"),
        "notice_tags": ", ".join(release.get("tag") or []),
        "tender_status": tender.get("status"),
        "value_amount": value.get("amount"),
        "value_currency": value.get("currency"),
        "deadline": tender_period.get("endDate"),
        "classification_scheme": classification.get("scheme"),
        "cpv_code": classification.get("id"),
        "category_description": classification.get("description"),
    }
    row["opportunity_status"] = "unknown"
    tags = release.get("tag") or []

    if "award" in tags or "awardUpdate" in tags:
        row["opportunity_status"] = "award_notice"

    elif tender.get("status") == "active" and "tender" in tags:
        deadline_text = tender_period.get("endDate")

        if deadline_text is not None:
            deadline = datetime.fromisoformat(deadline_text)

            if deadline <= now:
                row["opportunity_status"] = "review_needed"
            else:
                row["opportunity_status"] = "potential_opportunity"
    cpv_code = str(row["cpv_code"] or "")
    row["is_it"] = (
        row["classification_scheme"] == "CPV"
        and cpv_code.startswith(("72", "48", "302"))
    )
    rows.append(row)

            
print("Rows collected:", len(rows))
print("First row:", rows[0])

output_folder = project_folder / "data" / "processed"
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / "notices.csv"

with output_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("Saved:", output_file)

status_counts = {}

for row in rows:
    status = row["opportunity_status"]
    status_counts[status] = status_counts.get(status, 0) + 1

print("Status counts:", status_counts)

print("Tender fields:", releases[0]["tender"].keys())
print("Classification:", releases[0]["tender"].get("classification"))
print("Additional classifications:", releases[0]["tender"].get("additionalClassifications"))

shortlist = []

for row in rows:
    if row["is_it"] and row["opportunity_status"] in (
        "potential_opportunity",
        "review_needed",
    ):
        shortlist.append(row)

shortlist_file = output_folder / "it_shortlist.csv"

with shortlist_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(shortlist)

print("IT shortlist rows:", len(shortlist))
print("Shortlist saved:", shortlist_file)

for row in shortlist:
    print(
        row["title"],
        row["cpv_code"],
        row["deadline"],
        row["opportunity_status"],
        sep=" | ",
    )

release_ids = [row["release_id"] for row in rows]

print("Total rows:", len(rows))
print("Unique release IDs:", len(set(release_ids)))
print("Duplicate release IDs:", len(release_ids) - len(set(release_ids))) 

for field in ("release_id", "title", "buyer_name", "value_amount", "deadline", "cpv_code"):
    missing = 0

    for row in rows:
        if row[field] is None or row[field] == "":
            missing += 1

    print("Missing", field, ":", missing)