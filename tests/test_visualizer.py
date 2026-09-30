import json
import re
import shutil
import subprocess

import pytest

from app.config import ROOT
from app.models import QueryRequest
from app.pipeline import run_pipeline

QUESTIONS = [
    "What is the refund policy?", "Does Northstar Academy guarantee a job or salary?",
    "What is the lunar observatory telescope diameter?", "How many times can I resubmit a failed capstone?",
    "Can I pause my course?", "certificate attendance", "xyz",
]


def normalized(result: dict) -> dict:
    """Zero runtime timings so traces from separate executions are comparable."""
    result = json.loads(json.dumps(result))
    result["duration_ms"] = 0
    for event in result["events"]:
        event["elapsed_ms"] = 0
    return result


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required to execute the explorer's offline engine.")
def test_browser_offline_engine_matches_python_pipeline(tmp_path):
    """Run the explorer's embedded JavaScript engine and require identical traces."""
    html = (ROOT / "docs/architecture_visualizer.html").read_text()
    data = re.search(r'<script id="embedded-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    engine = html[html.index("// Offline engine"):html.index("// Online mode")]
    cases = [{"question": q, "max_retries": r, "top_k": k, "correction_demo": c}
             for q in QUESTIONS for r in (0, 2) for k in (1, 3, 6) for c in (False, True)]
    (tmp_path / "data.json").write_text(data)
    (tmp_path / "cases.json").write_text(json.dumps(cases))
    script = (f"const fs=require('fs');const DATA=JSON.parse(fs.readFileSync({json.dumps(str(tmp_path / 'data.json'))},'utf8'));"
              f"{engine}console.log(JSON.stringify(JSON.parse(fs.readFileSync({json.dumps(str(tmp_path / 'cases.json'))},'utf8')).map(runOffline)));")
    output = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    for case, browser in zip(cases, output, strict=True):
        assert normalized(browser) == normalized(run_pipeline(QueryRequest(**case))), case
