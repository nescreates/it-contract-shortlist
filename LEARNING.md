# Your first session

Goal: explain how one API request becomes a saved raw-data snapshot.

1. Run `python inspect_data.py data/raw/2026-10-01_sample`.
2. Open one raw page. Find `releases`, `id`, `ocid`, `tag`, `tender.status`, `tenderPeriod.endDate`, and `links.next`.
3. Explain why an awarded contract may still have a tender title, value and deadline.
4. Explain the difference between a release identifier and a procurement-process identifier.
5. Read `extract.py` and explain why raw bytes are saved before transformation.
6. Make one change you understand, inspect the result, then commit it in your own repository.

Do not claim a completed agent or proven time savings in a progress post. The honest first milestone is extracting and inspecting public procurement data. The interesting finding is that matching an IT category does not establish that a contract is open for bidding.

Next session: design the tables and write the first transformations together.
