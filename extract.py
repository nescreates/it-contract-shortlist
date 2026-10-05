"""Download unchanged Contracts Finder responses using Python's standard library."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

BASE = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search"


def extract(start, end, output, max_pages=3, page_size=100):
    if not 1 <= page_size <= 100 or max_pages < 1:
        raise ValueError("page_size must be 1–100 and max_pages must be positive")
    output.mkdir(parents=True, exist_ok=False)
    url = BASE + "?" + urlencode({"publishedFrom": start, "publishedTo": end,
                                  "limit": page_size})
    pages, seen = [], set()
    for number in range(1, max_pages + 1):
        if url in seen:
            raise ValueError("Repeated pagination URL; stopping to avoid a loop")
        seen.add(url)
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "www.contractsfinder.service.gov.uk":
            raise ValueError("Unexpected pagination host")
        if number > 1:
            time.sleep(4)
        request = Request(url, headers={"Accept": "application/json",
                                        "User-Agent": "ITContractShortlist/0.1"})
        try:
            with urlopen(request, timeout=45) as response:
                raw = response.read()
        except HTTPError as error:
            if error.code == 403:
                raise RuntimeError("HTTP 403: stop and wait at least five minutes before retrying, per API documentation") from error
            raise
        # Preserve bytes before parsing: malformed responses remain inspectable.
        filename = f"page_{number:03d}.json"
        (output / filename).write_bytes(raw)
        package = json.loads(raw)
        if not isinstance(package.get("releases"), list):
            raise ValueError("Response does not contain an OCDS releases list")
        next_url = (package.get("links") or {}).get("next")
        pages.append({"file": filename, "url": url,
                      "retrieved_at": datetime.now(timezone.utc).isoformat(),
                      "sha256": hashlib.sha256(raw).hexdigest(),
                      "release_count": len(package["releases"]),
                      "license": package.get("license")})
        manifest = {"source": BASE, "published_from": start, "published_to": end,
                    "pages": pages, "complete": not bool(next_url),
                    "next_url": next_url, "scope": "bounded sample; not a full catalogue"}
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Saved {filename}: {len(package['releases'])} releases")
        if not next_url:
            break
        url = urljoin(url, next_url)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="New folder; existing snapshots are never overwritten")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    extract(args.from_date, args.to_date, args.output, args.max_pages, args.page_size)
