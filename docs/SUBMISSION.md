# Submission handoff

## Required deliverables

- Complete working source and detailed README pushed to GitHub.
- YouTube explanation showing a successful first-pass query and correction/retry.
- Submit the actual GitHub repository URL and YouTube video URL.

## Publish the repository

From this project directory, first verify `git rev-parse --show-toplevel` points to **this project**, not a parent directory. If needed, initialize a dedicated repository with `git init -b main`. Do not stage an unrelated parent/home repository.

```bash
git add .
git status --short
git commit -m "Build Self-RAG with EURI evaluation and bounded retries"
gh repo create Self-RAG-With-Answer-Evaluation --public --source=. --remote=origin --push
```

If an existing remote repository is supplied, use its actual URL with `git remote add origin YOUR_REPOSITORY_URL` and `git push -u origin main` instead. Choose repository visibility intentionally. `.env`, `.venv`, and runtime artifacts must remain ignored.

## Before submitting

1. Run `python -m pytest -q`.
2. Run `python scripts/run_examples.py --mode live` using your own key; inspect the saved traces.
3. Check that the README renders and the full `docs/architecture_visualizer.html` is present.
4. Record the walkthrough in `VIDEO_SCRIPT.md`; disclose the controlled first-draft fault.
5. Upload the recording to YouTube and check playback and audio.
6. Open both links while signed out to confirm the marker can access them.

## Paste into the assignment portal

```text
GitHub Repository Link: [actual published repository URL]
YouTube Video Link: [actual uploaded video URL]
```

These are placeholders until you publish. A video script is preparation for the video, not an uploaded video.
