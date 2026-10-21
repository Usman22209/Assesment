"""
Test FastAPI endpoints using TestClient
"""
import sys
import os

sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_all():
    print("Testing GET /api/health...")
    r = client.get("/api/health")
    print(f"Health Status: {r.status_code}, Data: {r.json()}")
    assert r.status_code == 200

    print("\nTesting GET /api/stats...")
    r = client.get("/api/stats")
    print(f"Stats Status: {r.status_code}, Data: {r.json()}")
    assert r.status_code == 200

    print("\nTesting GET / (Frontend root)...")
    r = client.get("/")
    print(f"Frontend Status: {r.status_code}, Length: {len(r.text)}")
    assert r.status_code == 200
    assert "Dar Global" in r.text

    print("\nTesting POST /api/chat (Grounding Test)...")
    chat_payload = {
        "query": "What are the luxury villas in AIDA Oman and who designed the interiors?",
        "stream": False
    }
    r = client.post("/api/chat", json=chat_payload)
    print(f"Chat Status: {r.status_code}")
    data = r.json()
    print("Citations count:", len(data.get("citations", [])))
    for c in data.get("citations", []):
        print(f" - [{c['source']}] {c['title']} ({c['url']})")
    print("\nReply snippet:\n", data.get("reply", "")[:350], "...")

    print("\nALL API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all()
