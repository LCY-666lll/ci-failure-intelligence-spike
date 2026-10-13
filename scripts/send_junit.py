import argparse
import json
import os
import time
import urllib.request

from ci_failure_spike.auth import sign


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    body = open(args.report, "rb").read()
    timestamp = str(int(time.time()))
    metadata = json.dumps(
        {
            "repository": os.environ["GITHUB_REPOSITORY"],
            "run_id": os.environ["GITHUB_RUN_ID"],
            "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
            "commit_sha": os.environ["GITHUB_SHA"],
        },
        separators=(",", ":"),
    )
    request = urllib.request.Request(
        args.url.rstrip("/") + "/api/v1/ci-runs",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/xml",
            "X-CI-Timestamp": timestamp,
            "X-CI-Signature": sign(os.environ["INGEST_HMAC_SECRET"], timestamp, body),
            "X-CI-Metadata": metadata,
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        print(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()

