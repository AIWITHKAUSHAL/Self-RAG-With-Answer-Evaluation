"""Optional UI smoke test against a running local server using installed Chrome."""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    artifacts = ROOT / "artifacts" / "browser"
    artifacts.mkdir(parents=True, exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url)
        expect(page.locator("#documents .document")).to_have_count(6)
        page.screenshot(path=str(artifacts / "playground-desktop.png"), full_page=True)
        page.get_by_role("button", name="Run Self-RAG").click()
        expect(page.locator("#answer-badge")).to_have_text("EVALUATION PASSED")
        expect(page.locator("#metric-attempts")).to_have_text("1")
        expect(page.locator("#answer-text")).to_contain_text("7 calendar days")
        page.get_by_role("button", name="Trigger a correction").click()
        page.get_by_role("button", name="Run Self-RAG").click()
        expect(page.locator("#metric-attempts")).to_have_text("2")
        expect(page.locator("#answer-text")).to_contain_text("does not guarantee")
        expect(page.locator(".attempt-block")).to_have_count(2)
        page.locator(".attempt-block").first.get_by_text("Inspect draft", exact=True).click()
        page.screenshot(path=str(artifacts / "correction-desktop.png"), full_page=True)
        with page.expect_download() as download:
            page.get_by_role("button", name="Download trace").click()
        assert download.value.suggested_filename == "self-rag-trace.json"
        page.get_by_role("button", name="Missing evidence").click()
        page.get_by_role("button", name="Run Self-RAG").click()
        expect(page.locator("#answer-badge")).to_have_text("INSUFFICIENT EVIDENCE")
        expect(page.locator("#metric-attempts")).to_have_text("3")
        # Assert output is inserted as text even if a question contains HTML.
        page.locator("#question").fill("<img src=x onerror=alert(1)> refund policy")
        page.locator("#max-retries").select_option("0")
        page.get_by_role("button", name="Run Self-RAG").click()
        expect(page.locator("#trace-badge")).to_have_text("COMPLETED")
        expect(page.locator("#activity img")).to_have_count(0)
        page.goto(args.url + "/architecture")
        expect(page.locator(".node")).to_have_count(7)
        page.get_by_role("button", name="02 · Correction & retry").click()
        expect(page.locator("#attempts")).to_have_text("2")
        page.get_by_role("button", name="Next step").click()
        expect(page.locator("#step-count")).to_have_text("STEP 2 / 11")
        page.locator("#node-evaluate").click()
        expect(page.locator("#inspect-title")).to_have_text("Evaluate answer")
        expect(page.locator("#inspect-code")).to_contain_text("run_pipeline")
        page.locator("#speed").select_option("1000")
        page.get_by_role("button", name="▶ Play", exact=True).click()
        expect(page.locator("#step-count")).to_have_text("STEP 3 / 11", timeout=4000)
        page.get_by_role("button", name="Ⅱ Pause", exact=True).click()
        page.screenshot(path=str(artifacts / "architecture-desktop.png"), full_page=True)
        page.get_by_role("button", name="03 · Missing evidence").click()
        expect(page.locator("#attempts")).to_have_text("3")
        page.get_by_role("button", name="Reset", exact=True).click()
        expect(page.locator("#step-count")).to_have_text("STEP 1 / 13")
        # The generated artifact also works directly from disk, without the server.
        page.goto((ROOT / "docs/architecture_visualizer.html").as_uri())
        expect(page.locator("#question")).to_have_text("What is the refund policy?")
        expect(page.locator("#nodes .node")).to_have_count(7)
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(args.url)
        expect(page.locator("#documents .document")).to_have_count(6)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.get_by_role("button", name="Run Self-RAG").click()
        expect(page.locator("#answer-badge")).to_have_text("EVALUATION PASSED")
        page.screenshot(path=str(artifacts / "playground-mobile.png"), full_page=True)
        page.goto(args.url + "/architecture")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(artifacts / "architecture-mobile.png"), full_page=True)
        browser.close()
    assert not errors, errors
    print("Browser checks passed: desktop/mobile, three scenarios, trace download, safe rendering, explorer controls, and standalone HTML. Screenshots: artifacts/browser/")


if __name__ == "__main__":
    main()
