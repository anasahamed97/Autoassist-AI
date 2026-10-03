"""
AutoAssist AI - Interactive Retrieval Testing CLI
Runs sample queries against the RAG system and prints formatted results.
"""
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.rag.retriever import AutomotiveRetriever


def test_query(query: str, top_k: int = 3, threshold: float = 0.25):
    print("\n" + "=" * 70)
    print(f"QUERY: '{query}'")
    print(f"Parameters: Top-K={top_k}, Similarity Threshold={threshold}")
    print("=" * 70)

    retriever = AutomotiveRetriever()
    response = retriever.search(query=query, top_k=top_k, similarity_threshold=threshold)

    print(f"Retrieval Latency: {response.latency_ms:.2f} ms")
    print(f"Total Matches Found: {response.total_results}")

    if not response.results:
        print("\n[NO MATCH] No document sections met the similarity threshold.")
        return

    for idx, item in enumerate(response.results, start=1):
        print(f"\n--- [Result #{idx}] Similarity Score: {item.similarity:.4f} ---")
        print(f"Document Title : {item.document_title}")
        print(f"Manufacturer   : {item.manufacturer or 'N/A'}")
        print(f"Vehicle Model  : {item.vehicle_model or 'N/A'}")
        print(f"Section / Topic: {item.section or 'N/A'}")
        print(f"Page Number    : {item.page_number or 'N/A'}")
        print(f"Source         : {item.source or 'N/A'}")
        print("-" * 50)
        # Print content preview
        content_preview = item.content.strip()
        if len(content_preview) > 350:
            content_preview = content_preview[:350] + "..."
        print(content_preview)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test automotive RAG retrieval.")
    parser.add_argument("query", nargs="?", default="What can cause an engine to overheat?", help="Query string")
    parser.add_argument("--top-k", type=int, default=3, help="Top-K results")
    parser.add_argument("--threshold", type=float, default=0.25, help="Similarity threshold")
    args = parser.parse_args()

    test_query(args.query, top_k=args.top_k, threshold=args.threshold)
