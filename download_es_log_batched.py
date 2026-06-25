import requests
import json
from datetime import datetime

# ── Config ─────────────────────────────────────────────
KIBANA_URL   = "http://localhost:5601"
INDEX        = "my-index"
KIBANA_USER  = "elastic"
KIBANA_PASS  = "password"
BATCH_SIZE   = 1000
OUTPUT_FILE  = "output.txt"

HEADERS = {
    "kbn-xsrf": "true",
    "Content-Type": "application/json"
}

# ── Base Query ─────────────────────────────────────────
def build_query(search_after=None):
    query = {
        "track_total_hits": True,
        "query": {
            "bool": {
                "must": [
                    { "match_phrase": { "message": "your search text" } }
                ],
                "filter": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": "2024-01-01T00:00:00.000Z",
                                "lte": "2024-12-31T23:59:59.999Z",
                                "format": "strict_date_optional_time"
                            }
                        }
                    }
                ]
            }
        },
        "_source": ["message", "@timestamp", "label.mylabel1"],
        "sort": [
            { "@timestamp": { "order": "asc" } },
            { "_id":         { "order": "asc" } }
        ],
        "size": BATCH_SIZE
    }

    if search_after:
        query["search_after"] = search_after

    return query


# ── Fetch + Write Per Batch ─────────────────────────────
def fetch_and_write():
    url           = f"{KIBANA_URL}/api/console/proxy?path={INDEX}/_search&method=POST"
    search_after  = None
    batch_num     = 1
    total         = None
    total_written = 0

    print(f"Starting fetch at {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

    with open(OUTPUT_FILE, "w") as f:

        while True:

            # ── Fetch Batch ────────────────────────────
            try:
                query    = build_query(search_after)
                response = requests.post(
                    url,
                    headers=HEADERS,
                    auth=(KIBANA_USER, KIBANA_PASS),
                    json=query,
                    timeout=60
                )

                if response.status_code != 200:
                    print(f"Error {response.status_code}: {response.text}")
                    break

            except requests.exceptions.Timeout:
                print(f"Timeout on batch {batch_num}. Retrying...")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
                break

            data = response.json()
            hits = data["hits"]["hits"]

            # Print total on first batch
            if total is None:
                total = data["hits"]["total"]["value"]
                print(f"Total matching records : {total}")
                print("-" * 60)

            # No more records
            if not hits:
                print("No more records found.")
                break

            # ── Write Only 'message' Value Per Line ────
            for hit in hits:

                # Safely extract message value
                message = hit.get("_source", {}).get("message", None)

                if message is None:
                    print(f"  ⚠ Warning: missing 'message' in hit ID: {hit.get('_id')}")
                    continue

                f.write(message + "\n")     # ← one message per line, no JSON array

            total_written += len(hits)

            print(
                f"Batch {batch_num:>3} | "
                f"Fetched: {len(hits):>5} | "
                f"Written so far: {total_written:>6} / {total}"
            )

            # ── Set Cursor for Next Batch ──────────────
            search_after = hits[-1]["sort"]
            batch_num   += 1

            # Stop when all records written
            if total_written >= total:
                print("-" * 60)
                print(f"All {total_written} records written.")
                break

    print(f"\nSaved to '{OUTPUT_FILE}'")
    print(f"Finished at {datetime.now().strftime('%H:%M:%S')}")


# ── Main ────────────────────────────────────────────────
if __name__ == "__main__":
    fetch_and_write()
