"""Build a self-contained explorer from actual demo traces and source snapshots."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.models import QueryRequest
from app.pipeline import run_pipeline


def main():
    """Embed three offline traces and current source files in the HTML explorer.

    Normalizes runtime timings and escapes script-sensitive characters before
    writing docs/architecture_visualizer.html from the maintained template.
    """
    scenarios = {
        "first": run_pipeline(QueryRequest(question="What is the refund policy?")),
        "correction": run_pipeline(QueryRequest(question="Does Northstar Academy guarantee a job or salary?", correction_demo=True)),
        "missing": run_pipeline(QueryRequest(question="What is the lunar observatory telescope diameter?")),
    }
    # Timing is not useful for the teaching snapshot. Stable output is easier to review.
    for result in scenarios.values():
        result["duration_ms"] = 0
        for event in result["events"]:
            event["elapsed_ms"] = 0
    data = {"scenarios": scenarios, "sources": {name: (ROOT / name).read_text() for name in [
        "app/models.py", "app/retrieval.py", "app/providers.py", "app/pipeline.py", "app/main.py",
    ]}}
    template = (ROOT / "scripts/visualizer_template.html").read_text()
    encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    output = ROOT / "docs/architecture_visualizer.html"
    output.write_text(template.replace("__EMBEDDED_DATA__", encoded))
    print(f"Built {output.relative_to(ROOT)} with three real offline traces.")


if __name__ == "__main__":
    main()
