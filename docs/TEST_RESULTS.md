# Verification record

Verified locally on **2026-09-29** with Python 3.12, FastAPI 0.141.1, OpenAI Python SDK 2.54.0, pytest 9.1.1, and installed Google Chrome.

## Automated tests

Command: `python -m pytest -q`

**Result: 40 passed.** One dependency deprecation warning reports that Starlette intends to migrate its TestClient from httpx to httpx2; it does not affect the passing checks.

Coverage includes the first-pass path, actual bounded correction loop, all acceptance gates, removal of irrelevant documents, citation failures, zero and maximum retry budgets, no-evidence abstention, preservation of the original question, feedback propagation, strict judge schemas, incomplete document grades, exact EURI client configuration, sanitized errors, request validation, and HTTP routes/assets.

## Recorded offline examples

Command: `python scripts/run_examples.py --mode demo`

| Example | Observed result | Attempts | Additional retries |
|---|---|---:|---:|
| Refund policy | Accepted, with `refund-policy` citation | 1 | 0 |
| Employment guarantee with controlled bad draft | First draft rejected; corrected answer accepted | 2 | 1 |
| Telescope diameter outside the corpus | Abstained | 3 | 2 |

All three matched their expected behavior. JSON traces are available locally under ignored `artifacts/demo/` and are also embedded in the architecture visualizer with timing normalized for deterministic generation.

## Browser verification

Command: `python scripts/browser_smoke.py`

**Passed** in headless Google Chrome:

- Desktop: 1440 × 1100 viewport.
- Mobile: 390 × 844 viewport, no page-level horizontal overflow.
- Six documents loaded and rendered.
- First-pass answer, rejected-draft correction, and missing-evidence abstention.
- Trace JSON download.
- User-provided HTML rendered as text rather than executable markup.
- Architecture node inspector, scenario switching, next-step control, play/pause, speed, and reset.
- Standalone explorer opened directly from disk without a running API connection.
- No uncaught JavaScript page errors.

Screenshots were inspected; artifacts are stored locally under `artifacts/browser/`. README preview images are copied into `docs/images/`.

## Other checks

- Python source compilation passed.
- Frontend JavaScript syntax check passed.
- Generated architecture explorer contains actual current source snapshots and pipeline traces.
- `.env`, `.venv`, and runtime artifacts are ignored by Git.

## Live EURI verification status

**Not completed: no EURI_API_KEY was available.** Running the live example runner stopped with the intended configuration error before making API calls. No live response, model-access verification, or live success is claimed here. Add a valid key privately and run:

```bash
python scripts/euri_example.py
python scripts/run_examples.py --mode live
```

The live runner validates the observed outcomes and saves their real traces separately from the offline examples. Provider contract tests use a fake client and do not verify remote service availability.

Docker packaging and GitHub Actions configuration are included but have not been executed here. GitHub publication and an actual recorded/uploaded YouTube explanation remain separate submission steps.
