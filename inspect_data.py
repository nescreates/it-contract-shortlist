"""Inspect saved responses offline. This is discovery, not the final data model."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def inspect(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    records = []
    for page in manifest["pages"]:
        raw = (folder / page["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != page["sha256"]:
            raise ValueError(f"Snapshot checksum mismatch: {page['file']}")
        records.extend(json.loads(raw)["releases"])
    ids = [r.get("id") for r in records if r.get("id")]
    ocids = [r.get("ocid") for r in records if r.get("ocid")]
    return {
        "release_count": len(records), "unique_release_ids": len(set(ids)),
        "unique_process_ids": len(set(ocids)),
        "duplicate_release_ids": len(ids) - len(set(ids)),
        "stages": dict(Counter(tag for r in records for tag in r.get("tag", []))),
        "statuses": dict(Counter((r.get("tender") or {}).get("status", "missing") for r in records)),
        "missing_deadline": sum(not ((r.get("tender") or {}).get("tenderPeriod") or {}).get("endDate") for r in records),
        "missing_tender_amount": sum(((r.get("tender") or {}).get("value") or {}).get("amount") is None for r in records),
        "complete_date_window": manifest["complete"],
        "it_classification_examples": [
            {"release_id": r.get("id"), "title": (r.get("tender") or {}).get("title"),
             "tags": r.get("tag"), "status": (r.get("tender") or {}).get("status")}
            for r in records if any(str(c.get("id", "")).startswith(("72", "48"))
                                    and c.get("scheme") == "CPV"
                                    for c in [(r.get("tender") or {}).get("classification") or {}]
                                    + ((r.get("tender") or {}).get("additionalClassifications") or []))
        ][:10],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.folder), indent=2, ensure_ascii=False))
