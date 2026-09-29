import argparse
import json

from app.models import QueryRequest
from app.pipeline import run_pipeline
from app.providers import ProviderError


def main():
    parser = argparse.ArgumentParser(description="Self-RAG demo / live EURI runner")
    parser.add_argument("question", nargs="?", default="What is the refund policy?")
    parser.add_argument("--mode", choices=["demo", "live"], default="demo")
    parser.add_argument("--max-retries", type=int, choices=range(5), default=2)
    parser.add_argument("--correction-demo", action="store_true")
    args = parser.parse_args()
    try:
        result = run_pipeline(QueryRequest(question=args.question, mode=args.mode, max_retries=args.max_retries, correction_demo=args.correction_demo))
    except ProviderError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
