"""
Test script for RAGEngine
"""
import sys
import os

sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.rag_engine import RAGEngine

def main():
    rag = RAGEngine(data_path="data/knowledge_base.json")
    print(f"Total chunks indexed: {len(rag.chunks)}")

    test_queries = [
        "Tell me about Trump Simaisma in Qatar",
        "How do auctions work on Wasalt and what is the e-wallet?",
        "What luxury villas in Oman are by Fendi Casa?",
        "What is Dar Global GDV and financial growth?",
        "Can you compare Wasalt and Dar Global?",
        "What are the requirements for Fal license in Saudi Arabia?"
    ]

    for q in test_queries:
        results = rag.search(q, top_k=2)
        print(f"\n=== Query: {q} ===")
        for r in results:
            print(f"  * [{r['source']}] {r['title']} (Score: {r['score']})")
            print(f"    URL: {r['url']}")
            print(f"    Snippet: {r['text'][:120]}...")

if __name__ == "__main__":
    main()
