# YouTube explanation: Self-RAG with Answer Evaluation

Target length: 6–8 minutes. Record the browser and editor, with your own spoken explanation. Use a title such as **Self-RAG with Answer Evaluation | EURI Gemini | Retry & Hallucination Checks**.

## Before recording

1. Install dependencies, add `EURI_API_KEY` privately to `.env`, and start the server.
2. Run `python -m pytest -q` and `python scripts/run_examples.py --mode live`.
3. Verify saved live traces show the intended first-pass and correction outcomes. Live judgments may vary; explain observed results honestly.
4. Open the playground, architecture explorer, `app/pipeline.py`, and `app/providers.py` in separate tabs.
5. Keep `.env`, shell history, and credentials out of the recording. Hide unrelated private windows.

## 0:00–0:45 — Problem and overview

“Ordinary RAG can retrieve context and still produce an unsupported answer. My agent treats its first answer as a draft. It checks document relevance, answer relevance, and grounding. A bad draft triggers rewriting and retrieval again. A retry budget prevents an infinite loop.”

Show the playground and name the requested model: `gemini-3.5-flash-lite`, served through EURI using the OpenAI Python client.

## 0:45–1:45 — Walk through the architecture

Open `/architecture`. Select **First-pass success**, press Play, then pause on **Grade documents** and **Evaluate answer**.

Explain:

- Local BM25 retrieves a few passages; it does not call an embedding API.
- Live EURI document grading keeps relevant passages.
- Generation uses only those passages and requires citations.
- A separate evaluation call checks answer relevance and every factual claim's grounding.
- Click **Rewrite & retry** to show feedback and the loop.

State explicitly: “This visualizer plays recorded offline traces with embedded source code. Next I’ll run fresh model calls in the playground.”

## 1:45–2:45 — Successful first-pass query

Select **Live · EURI / Gemini**, turn correction demo **off**, and ask:

> What is the refund policy?

Show the result, cited refund document, attempt count, relevance and grounding scores. Expand the retrieved context and grading details. Point out the 7-calendar-day window and less-than-20%-completion condition in the source. Explain why every acceptance gate passed.

If no valid live key is available, select Offline demo and say clearly that you are showing an extractive simulation. Do not call an offline recording a live model demonstration.

## 2:45–4:15 — Deliberate unsupported draft and recovery

Click **Trigger a correction**. Ensure at least one retry is allowed. Explain the flag before running:

“For a repeatable test, I deliberately replace the first draft with a false employment and ₹50 lakh salary guarantee. The evaluator still makes its own decision. This is fault injection, not a claim that the model naturally produced the error.”

Run the query. Expand attempt one:

1. Read the injected draft.
2. Compare it with the career-support source, which explicitly says no employment or salary guarantee.
3. Show the low grounding score or unsupported claims and evaluator feedback.
4. Show the rewritten query.
5. Expand attempt two to prove fresh retrieval and document grading occurred.
6. Show the corrected answer and source citation.

Explain that `correction_demo` is off for normal usage; genuine failed evaluations take the same retry path.

## 4:15–5:00 — Stopping without evidence

Click **Missing evidence** with a retry limit of 2. Ask:

> What is the lunar observatory telescope diameter?

Show three attempts followed by abstention. Explain that “two retries” means the initial attempt plus two extra attempts. No rejected draft is promoted to the final answer. If there is no relevant context, generation is skipped entirely.

## 5:00–6:30 — Code walkthrough

Show `app/pipeline.py`:

- `for index in range(request.max_retries + 1)` gives a finite loop.
- `provider.grade(...)` and the document threshold filter context.
- `provider.generate(...)` receives previous feedback.
- `provider.evaluate(...)` independently audits the draft.
- Acceptance requires answer relevance, grounding, support, no unsupported claims, and valid citations.
- Only `finish("accepted", ...)` returns a draft; otherwise the final response is abstention.

Show `app/providers.py`: client configuration, prompts, strict JSON parsing, and safe error handling. Explain that the user question stays unchanged while the retrieval query evolves.

## 6:30–7:15 — Tests, limitations, and repository

Run `python -m pytest -q`. Briefly explain tests for incorrect citations, malformed judge output, retry limits, and the correction cycle. Show the detailed README and runnable examples.

“The live judge is useful but not perfect; it uses the same underlying model as the generator. The local retriever is lexical, and the offline demo is intentionally simpler. All intermediate evidence is inspectable so the decisions can be reviewed.”

End with the actual GitHub repository URL and explain how to start the app. Upload to YouTube as public or unlisted and confirm the link works when signed out.

## Suggested YouTube description

```text
Self-RAG with Answer Evaluation using EURI and gemini-3.5-flash-lite.

GitHub: [paste your published repository URL]

Demonstrates:
- Retrieval and document relevance grading
- First-pass supported answer
- Explicit fault injection, grounding rejection, and correction
- Bounded retries and abstention when evidence is missing
- Interactive architecture explorer and automated tests

The correction demonstration intentionally inserts one unsupported draft.
The video identifies whether each run uses live EURI or the offline demo.
```
