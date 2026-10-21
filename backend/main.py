"""
Entry point for running the Dar Global & Wasalt Chatbot application server.
Supports dynamic PORT configuration for Docker, Render, and Hugging Face Spaces.
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting Dar Global & Wasalt AI Assistant on {host}:{port}")
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)
