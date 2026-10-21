"""
RAG Engine: Document Chunking, Hybrid Retrieval, and Grounding Context Generation.
Provides fast, accurate, and source-grounded retrieval for Dar Global & Wasalt data.
"""

import json
import logging
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("RAG")


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        source: str,
        title: str,
        url: str,
        category: str,
        text: str,
        tags: List[str],
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.source = source
        self.title = title
        self.url = url
        self.category = category
        self.text = text
        self.tags = tags

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "category": self.category,
            "text": self.text,
            "tags": self.tags,
        }


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean lowercase words."""
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    words = cleaned.split()
    # Filter very short words
    return [w for w in words if len(w) > 1]


class RAGEngine:
    def __init__(self, data_path: str = "data/knowledge_base.json", chunk_size: int = 450, chunk_overlap: int = 100):
        self.data_path = data_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks: List[DocumentChunk] = []
        self.docs: List[Dict[str, Any]] = []

        # BM25 Index Data Structures
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}  # term -> [(chunk_idx, term_count)]

        self.load_and_index()

    def load_and_index(self):
        """Loads knowledge base and builds hybrid retrieval index."""
        if not os.path.exists(self.data_path):
            logger.warning(f"Knowledge base file not found at {self.data_path}. Index will be empty.")
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            self.docs = json.load(f)

        self.chunks.clear()
        self.inverted_index.clear()
        self.doc_freqs.clear()

        for doc in self.docs:
            self._chunk_document(doc)

        logger.info(f"Loaded {len(self.docs)} documents, created {len(self.chunks)} chunks.")
        self._build_bm25_index()

    def _chunk_document(self, doc: Dict[str, Any]):
        """Splits document content into overlapping semantic chunks."""
        content = doc.get("content", "")
        # Split by paragraphs or sentence boundaries
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

        current_chunk = []
        current_len = 0

        for para in paragraphs:
            para_words = para.split()
            if not para_words:
                continue

            if current_len + len(para_words) <= self.chunk_size:
                current_chunk.append(para)
                current_len += len(para_words)
            else:
                # If current chunk has content, save it
                if current_chunk:
                    chunk_text = "\n".join(current_chunk)
                    chunk_id = f"{doc['id']}_c{len(self.chunks)}"
                    self.chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=doc["id"],
                            source=doc.get("source", "Unknown"),
                            title=doc.get("title", "Untitled"),
                            url=doc.get("url", ""),
                            category=doc.get("category", "General"),
                            text=chunk_text,
                            tags=doc.get("tags", []),
                        )
                    )

                # Start new chunk with overlap if possible
                overlap_words = current_chunk[-1].split()[-self.chunk_overlap:] if current_chunk else []
                current_chunk = [" ".join(overlap_words), para] if overlap_words else [para]
                current_len = len(overlap_words) + len(para_words)

        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunk_id = f"{doc['id']}_c{len(self.chunks)}"
            self.chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc["id"],
                    source=doc.get("source", "Unknown"),
                    title=doc.get("title", "Untitled"),
                    url=doc.get("url", ""),
                    category=doc.get("category", "General"),
                    text=chunk_text,
                    tags=doc.get("tags", []),
                )
            )

    def _build_bm25_index(self):
        """Builds an inverted index and computes BM25 parameters."""
        total_chunks = len(self.chunks)
        if total_chunks == 0:
            return

        self.doc_lengths = []
        total_len = 0

        for idx, chunk in enumerate(self.chunks):
            # Include title, tags, and category in indexable text for higher recall
            combined_text = f"{chunk.title} {chunk.category} {' '.join(chunk.tags)} {chunk.text}"
            tokens = tokenize(combined_text)
            self.doc_lengths.append(len(tokens))
            total_len += len(tokens)

            # Count term frequencies
            tf_map: Dict[str, int] = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            for term, count in tf_map.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((idx, count))
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avg_doc_len = total_len / total_chunks if total_chunks > 0 else 1.0

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_filter: Optional[str] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 hybrid search over the index.
        Applies title and domain keyword boosting.
        """
        if not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        total_chunks = len(self.chunks)
        scores: Dict[int, float] = {}

        # Important domain entities to boost
        boost_keywords = {
            "aida": 2.5,
            "simaisma": 2.5,
            "trump": 2.5,
            "fendi": 2.5,
            "pagani": 2.5,
            "lamborghini": 2.5,
            "missoni": 2.5,
            "w": 1.5,
            "residences": 1.5,
            "rayana": 2.5,
            "safar": 2.5,
            "diriyah": 2.5,
            "wasalt": 2.0,
            "darglobal": 2.0,
            "dar": 1.5,
            "global": 1.5,
            "auction": 2.5,
            "auctions": 2.5,
            "ewallet": 2.5,
            "wallet": 2.0,
            "riyadh": 2.0,
            "jeddah": 2.0,
            "dammam": 2.0,
            "fal": 2.5,
            "rega": 2.5,
            "maldives": 2.5,
            "noonu": 2.5,
            "gdv": 2.0,
            "lse": 2.0,
            "revenue": 1.8,
            "billion": 1.8,
        }

        for term in query_tokens:
            if term not in self.inverted_index:
                continue

            df = self.doc_freqs.get(term, 0)
            # Standard BM25 IDF formula
            idf = math.log(1.0 + (total_chunks - df + 0.5) / (df + 0.5))
            boost = boost_keywords.get(term, 1.0)

            for chunk_idx, tf in self.inverted_index[term]:
                doc_len = self.doc_lengths[chunk_idx]
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                term_score = idf * (numerator / denominator) * boost
                scores[chunk_idx] = scores.get(chunk_idx, 0.0) + term_score

        # Also apply title/category/source exact match boost
        query_lower = query.lower()
        for idx in list(scores.keys()):
            chunk = self.chunks[idx]

            # Filter by source if requested ("Dar Global" or "Wasalt")
            if source_filter and source_filter.lower() not in chunk.source.lower():
                scores[idx] = -1.0
                continue

            # Title matching bonus
            title_lower = chunk.title.lower()
            for token in query_tokens:
                if token in title_lower:
                    scores[idx] += 1.5

            # Exact phrase bonus
            if query_lower in chunk.text.lower() or query_lower in title_lower:
                scores[idx] += 3.0

        # Sort by highest score
        ranked_indices = sorted(
            [idx for idx, score in scores.items() if score > 0],
            key=lambda i: scores[i],
            reverse=True,
        )

        results = []
        for idx in ranked_indices[:top_k]:
            chunk = self.chunks[idx]
            res = chunk.to_dict()
            res["score"] = round(scores[idx], 4)
            results.append(res)

        return results

    def build_grounded_prompt(self, user_query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks into a prompt grounding block."""
        if not retrieved_chunks:
            return (
                "CONTEXT:\n"
                "No specific context found in the Dar Global or Wasalt database for this query.\n\n"
                f"USER QUERY: {user_query}\n"
            )

        context_blocks = []
        for i, c in enumerate(retrieved_chunks, 1):
            context_blocks.append(
                f"[Source {i}: {c['source']} | Title: {c['title']} | Category: {c['category']} | URL: {c['url']}]\n"
                f"{c['text']}\n"
            )

        context_str = "\n---\n".join(context_blocks)
        return (
            f"RELEVANT VERIFIED CONTEXT FROM DAR GLOBAL & WASALT:\n\n"
            f"{context_str}\n\n"
            f"---\n"
            f"USER QUERY: {user_query}\n"
        )
