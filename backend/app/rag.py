from __future__ import annotations
import json
from dataclasses import dataclass
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from app.config import settings


@dataclass
class Chunk:
    text: str
    source: str
    page: int


def chunk_text(text: str, size: int = 700, overlap: int = 120) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []
    chunks, start = [], 0
    while start < len(clean):
        end = min(start + size, len(clean))
        piece = clean[start:end]
        if end < len(clean):
            boundary = max(piece.rfind(". "), piece.rfind(" "))
            if boundary > size * 0.55:
                end = start + boundary + 1
                piece = clean[start:end]
        chunks.append(piece.strip())
        if end >= len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


class RAGStore:
    def __init__(self):
        self.model = None
        self.index = None
        self.chunks = []
        self.index_file = settings.vector_path / "kb.faiss"
        self.meta_file = settings.vector_path / "metadata.json"

    def _ensure_model(self):
        if self.model is None:
            self.model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2")

    def _load_pdfs(self):
        chunks = []
        for pdf in sorted(settings.kb_path.glob("*.pdf")):
            reader = PdfReader(str(pdf))
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                for piece in chunk_text(text):
                    chunks.append(Chunk(piece, pdf.name, page_num))
        return chunks

    def build(self):
        self._ensure_model()
        settings.vector_path.mkdir(parents=True, exist_ok=True)
        self.chunks = self._load_pdfs()
        if not self.chunks:
            raise RuntimeError(f"No PDF documents found in {settings.kb_path}")
        embeddings = self.model.encode(
            [c.text for c in self.chunks], normalize_embeddings=True, show_progress_bar=False)
        arr = np.asarray(embeddings, dtype="float32")
        self.index = faiss.IndexFlatIP(arr.shape[1])
        self.index.add(arr)
        faiss.write_index(self.index, str(self.index_file))
        self.meta_file.write_text(json.dumps(
            [c.__dict__ for c in self.chunks], indent=2), encoding="utf-8")

    def load_or_build(self):
        self._ensure_model()
        if self.index_file.exists() and self.meta_file.exists():
            self.index = faiss.read_index(str(self.index_file))
            self.chunks = [
                Chunk(**x) for x in json.loads(self.meta_file.read_text(encoding="utf-8"))]
        else:
            self.build()

    def search(self, query: str, k: int = 5):
        if self.index is None:
            self.load_or_build()

        q = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False
        )

        # Retrieve extra candidates first
        candidate_k = min(max(k * 3, 12), len(self.chunks))

        scores, ids = self.index.search(
            np.asarray(q, dtype="float32"),
            candidate_k
        )

        query_lower = query.lower()

        preferred_sources = set()

        if any(x in query_lower for x in [
            "price", "pricing", "cost",
            "premium", "basic", "business",
            "compare", "plan", "feature"
        ]):
            preferred_sources.update([
                "Pricing.pdf",
                "Products.pdf"
            ])

        if any(x in query_lower for x in [
            "refund", "charged", "payment",
            "invoice", "subscription", "paid"
        ]):
            preferred_sources.update([
                "RefundPolicy.pdf",
                "Pricing.pdf"
            ])

        if any(x in query_lower for x in [
            "login", "password", "install",
            "error", "crash", "locked"
        ]):
            preferred_sources.update([
                "InstallationGuide.pdf",
                "UserManual.pdf"
            ])

        if any(x in query_lower for x in [
            "shipping", "delivery", "tracking"
        ]):
            preferred_sources.add("ShippingPolicy.pdf")

        if any(x in query_lower for x in [
            "warranty", "repair", "defect"
        ]):
            preferred_sources.add("Warranty.pdf")

        if any(x in query_lower for x in [
            "hours", "contact", "support",
            "company", "policy"
        ]):
            preferred_sources.add("FAQ.pdf")

        results = []

        for score, idx in zip(scores[0], ids[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue

            c = self.chunks[idx]

            adjusted_score = float(score)

            # Small domain bonus for the most likely company document
            if c.source in preferred_sources:
                adjusted_score += 0.08

            results.append({
                "text": c.text,
                "source": c.source,
                "page": c.page,
                "score": adjusted_score
            })

        results.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # Prefer domain-relevant documents when we know the likely source.
        if preferred_sources:
            preferred_results = [
                item for item in results
                if item["source"] in preferred_sources
            ]

            other_results = [
                item for item in results
                if item["source"] not in preferred_sources
            ]

            results = preferred_results + other_results

        filtered = []
        seen = set()

        for item in results:
            key = (
                item["source"],
                item["page"],
                item["text"][:100]
            )

            if key in seen:
                continue

            seen.add(key)

            if item["score"] >= 0.20:
                filtered.append(item)

            if len(filtered) >= k:
                break

        return filtered

        # Remove weak and duplicate-looking results
        filtered = []

        seen = set()

        for item in results:
            key = (
                item["source"],
                item["page"],
                item["text"][:100]
            )

            if key in seen:
                continue

            seen.add(key)

            if item["score"] >= 0.20:
                filtered.append(item)

            if len(filtered) >= k:
                break

        return filtered


rag_store = RAGStore()
