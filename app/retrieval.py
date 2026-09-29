"""Small, reproducible BM25 retriever. No embedding API or model download."""
import json
import math
import re
from collections import Counter

from app.config import ROOT
from app.models import Document

STOP_WORDS = set("a an the is are was were to of in on at for and or i my me it its do does how what can with within have has please tell about academy northstar".split())


def tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]


class Retriever:
    def __init__(self, documents: list[Document] | None = None):
        self.documents = documents if documents is not None else [
            Document(**item) for item in json.loads((ROOT / "data/knowledge_base.json").read_text())
        ]
        if len({doc.id for doc in self.documents}) != len(self.documents):
            raise ValueError("Document IDs must be unique.")
        self.counts = [Counter(tokens(doc.title + " " + doc.text)) for doc in self.documents]
        self.lengths = [sum(count.values()) for count in self.counts]
        self.average = sum(self.lengths) / max(1, len(self.lengths)) or 1

    def search(self, query: str, top_k: int) -> list[dict]:
        ranked = []
        for doc, counts, length in zip(self.documents, self.counts, self.lengths):
            score = 0.0
            for token in set(tokens(query)):
                frequency = counts[token]
                containing = sum(token in count for count in self.counts)
                idf = math.log(1 + (len(self.documents) - containing + 0.5) / (containing + 0.5))
                score += idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * length / self.average))
            if score > 0:
                ranked.append({"document": doc, "score": round(score, 4)})
        return sorted(ranked, key=lambda item: item["score"], reverse=True)[:top_k]
