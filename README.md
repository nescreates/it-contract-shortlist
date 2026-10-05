# IT Contract Shortlist — first draft

## What I built and who for
A Python pipeline for a small IT services business reviewing public procurement notices. It transforms saved Contracts Finder API responses into a consistent table, distinguishes award notices from tender notices, checks tender deadlines, and identifies IT categories using CPV codes.

The outputs are:
- `data/processed/notices.csv`: all 300 notices with category and opportunity-status fields.
- `data/processed/it_shortlist.csv`: IT tender notices marked as potential opportunities or needing review.

At the fixed reference time of 5 October 2026, 11:00 UTC, the sample produces two IT notices needing review because their deadlines have passed. It contains no shortlisted IT notices with future deadlines. The shortlist supports human review; it does not confirm that a business can bid.

## The data

Source: [Contracts Finder OCDS API](https://www.contractsfinder.service.gov.uk/apidocumentation/Notices/1/GET-Published-Notice-OCDS-Search).

The API exposes procurement releases, not a ready-made list of open opportunities. The current reference documents `publishedFrom`, `publishedTo`, `limit` (1–100) and a pagination cursor. Use the returned `links.next` unchanged and specify both date bounds. No API credentials are included.

Data attribution: Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Source: Contracts Finder, Cabinet Office. Each saved package records its source licence. Code and data licensing are separate; no third-party attachment files are downloaded.

## How it works

1. Request a bounded publication-date window, including all stages for discovery.
2. Save response bytes unchanged, then validate the JSON structure.
3. Follow pagination with a four-second gap, up to an explicit sample cap.
4. Record request URLs, retrieval timestamps, checksums and completeness in a separate manifest.
5. Inspect the raw snapshot offline for stages, status, missing values and repeated identifiers.

The cap is not a claim of complete coverage. An existing snapshot directory is never overwritten. On HTTP 403, the extractor stops and tells the operator to wait at least five minutes, as the source documentation specifies. No automatic retry storm is attempted.
 
 ### Transformation and shortlist rules

`explore.py` loads the saved JSON pages and creates one row per release.

- Tags containing `award` or `awardUpdate` become `award_notice`.
- Active notices tagged `tender` are checked against a fixed reference time: 5 October 2026, 11:00 UTC.
- Deadlines at or before that time become `review_needed`.
- Future deadlines become `potential_opportunity`.
- Missing deadlines and notices outside these rules remain `unknown`.
- Main CPV codes beginning with `72`, `48`, or `302` are flagged as IT.
- The shortlist includes IT rows labelled `potential_opportunity` or `review_needed`.

Missing values remain blank in the CSV. Missing amounts are not replaced with zero.

### Checks and results

The sample contains 300 rows and 300 unique release IDs, with no duplicate release IDs.

There are 59 missing amounts and 4 missing deadlines. No release IDs, titles, buyer names, or main CPV codes are missing.

The status counts are:
- 279 award notices
- 6 notices needing review
- 10 potential opportunities
- 5 unknown

The IT shortlist contains 2 notices, both needing review.


## How to run it

Python 3.10 or newer; no third-party dependencies for this milestone. From this directory:

To regenerate both CSV outputs from the saved sample, run from the project directory:

```bash
python3 explore.py
```

This runs offline without API keys or third-party packages.


```bash
python inspect_data.py data/raw/2026-10-01_sample
```

For a fresh snapshot, use a new destination folder:

```bash
python extract.py --from-date 2026-09-24T00:00:00Z --to-date 2026-10-01T13:00:00Z --output data/raw/my_new_sample --max-pages 3
```

The first command runs without internet or credentials. The second requires live API access. A source outage or access restriction should not block offline inspection.

- Check additional CPV classifications, rather than only the main category.
- Handle amendments and related releases together so older notices do not mislead users.
- Add source links and check procurement restrictions and eligibility.
- Handle invalid deadlines and missing timezones explicitly.
- Add automated checks for deadline boundaries, missing fields, and duplicates.
- Store typed data in DuckDB and make the reference time configurable.

Limitations: this is a capped 300-release sample, not complete market coverage. The shortlist uses individual releases and main CPV categories. A future deadline does not confirm that bidding is available. `review_needed` means the published deadline has passed and further checking is required.





## Where AI helped

Codex generated the initial extraction and profiling scripts and helped inspect the API documentation. It also provided step-by-step code suggestions and explanations for the transformation, classification, CSV exports, and data-quality checks, and helped draft this README.

I ran the code locally and inspected the outputs. My decisions included distinguishing award notices from tender invitations, retaining unknown classifications where information was insufficient, and marking passed deadlines for review rather than assuming they remained open.