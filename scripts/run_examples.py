"""Run and save first-pass, controlled correction, and missing-evidence examples."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models import QueryRequest
from app.pipeline import run_pipeline
from app.providers import ProviderError


def main():
    """Run three scenarios in the selected mode and save their actual JSON traces.

    Exit with status 1 on a provider failure or an unexpected scenario outcome.
    Live executions require a configured key and consume EURI API quota.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    args = parser.parse_args()
    folder = ROOT / "artifacts" / args.mode
    folder.mkdir(parents=True, exist_ok=True)
    scenarios = [
        ("first-pass", "What is the refund policy?", False),
        ("correction", "Does Northstar Academy guarantee a job or salary?", True),
        ("missing-evidence", "What is the lunar observatory telescope diameter?", False),
    ]
    failures = []
    for name, question, correction in scenarios:
        print(f"Running {name} in {args.mode} mode…", flush=True)
        try:
            result = run_pipeline(QueryRequest(question=question, mode=args.mode, correction_demo=correction))
        except ProviderError as error:
            parser.exit(1, f"{error}\n")
        output = folder / f"{name}.json"
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"  {result['status']} · {result['attempt_count']} attempts · saved {output.relative_to(ROOT)}", flush=True)
        if name == "first-pass" and (result["status"] != "accepted" or result["attempt_count"] != 1):
            failures.append("First-pass example did not pass on its first attempt.")
        if name == "correction" and (result["status"] != "accepted" or result["attempt_count"] < 2 or result["attempts"][0]["accepted"]):
            failures.append("Correction example did not demonstrate rejection followed by acceptance.")
        if name == "missing-evidence" and result["status"] != "abstained":
            failures.append("Missing-evidence example unexpectedly produced an accepted answer.")
    if failures:
        parser.exit(1, "\n".join(failures) + "\nInspect the saved traces; live model judgments can vary.\n")
    print("All three scenarios matched their expected behavior.")


if __name__ == "__main__":
    main()
