"""
FastAPI Application for Dar Global & Wasalt AI Chatbot.
Provides RAG-grounded chat, knowledge base search, and streaming responses.
"""

import utils.clients
import utils.http_session
import utils.transport
import utils.session
import json
import logging
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.llm_client import DEFAULT_FREE_MODELS, OpenRouterClient
from backend.rag_engine import RAGEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("App")

app = FastAPI(
    title="Dar Global & Wasalt AI Assistant",
    description="Grounded AI Chatbot for Dar Global luxury real estate and Wasalt Saudi PropTech marketplace.",
    version="1.0.0",
)

# Enable CORS for local testing and cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine and OpenRouter Client
rag_engine = RAGEngine(data_path="data/knowledge_base.json")
llm_client = OpenRouterClient()


# Request / Response Schemas
class Message(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    query: str = Field(..., description="User query")
    history: Optional[List[Message]] = Field(default=[], description="Chat conversation history")
    source_filter: Optional[str] = Field(default=None, description="Optional filter: 'Dar Global' or 'Wasalt'")
    model: Optional[str] = Field(default=None, description="Specific OpenRouter free model to use")
    user_api_key: Optional[str] = Field(default=None, description="User-supplied OpenRouter API key")
    top_k: Optional[int] = Field(default=4, description="Number of retrieved chunks")
    stream: Optional[bool] = Field(default=False, description="Whether to stream response")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search term")
    source_filter: Optional[str] = Field(default=None, description="Optional source filter")
    top_k: Optional[int] = Field(default=5, description="Number of search results")


# Endpoints
@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "Dar Global & Wasalt AI Assistant",
        "chunks_indexed": len(rag_engine.chunks),
        "docs_count": len(rag_engine.docs),
        "default_model": llm_client.default_model,
        "has_server_key": bool(llm_client.api_key),
    }


@app.get("/api/stats")
async def get_stats():
    docs = rag_engine.docs
    dg_count = sum(1 for d in docs if "Dar Global" in d.get("source", ""))
    wasalt_count = sum(1 for d in docs if "Wasalt" in d.get("source", ""))
    categories = sorted(list(set(d.get("category", "General") for d in docs)))

    return {
        "total_documents": len(docs),
        "total_chunks": len(rag_engine.chunks),
        "dar_global_documents": dg_count,
        "wasalt_documents": wasalt_count,
        "categories": categories,
        "supported_models": DEFAULT_FREE_MODELS,
    }


@app.get("/api/models")
async def get_models():
    return {
        "free_models": DEFAULT_FREE_MODELS,
        "current_default": llm_client.default_model,
    }


@app.post("/api/search")
async def search_knowledge_base(req: SearchRequest):
    results = rag_engine.search(
        query=req.query,
        top_k=req.top_k,
        source_filter=req.source_filter,
    )
    return {"query": req.query, "results": results, "count": len(results)}


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    # 1. Retrieve most relevant context chunks
    retrieved = rag_engine.search(
        query=req.query,
        top_k=req.top_k,
        source_filter=req.source_filter,
    )

    # 2. Build grounded prompt
    grounded_user_content = rag_engine.build_grounded_prompt(req.query, retrieved)

    # 3. Assemble message history
    messages_payload = []
    if req.history:
        for m in req.history[-6:]:  # Keep recent context
            messages_payload.append({"role": m.role, "content": m.content})

    messages_payload.append({"role": "user", "content": grounded_user_content})

    # 4. Stream or standard response
    if req.stream:
        async def event_generator():
            # Send citations first as metadata event
            citations = [
                {
                    "source": c["source"],
                    "title": c["title"],
                    "url": c["url"],
                    "category": c["category"],
                    "snippet": c["text"][:200] + "...",
                }
                for c in retrieved
            ]
            yield f"event: citations\ndata: {json.dumps(citations)}\n\n"

            async for token in llm_client.stream_response(
                messages=messages_payload,
                model=req.model,
                user_key=req.user_api_key,
            ):
                yield f"event: message\ndata: {json.dumps({'token': token})}\n\n"

            yield "event: end\ndata: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Standard non-streaming response
    generation = await llm_client.generate_response(
        messages=messages_payload,
        model=req.model,
        user_key=req.user_api_key,
    )

    citations = [
        {
            "source": c["source"],
            "title": c["title"],
            "url": c["url"],
            "category": c["category"],
            "snippet": c["text"][:200] + "...",
        }
        for c in retrieved
    ]

    return {
        "reply": generation["content"],
        "model_used": generation.get("model_used", "default"),
        "citations": citations,
        "success": generation.get("success", True),
    }


# Mount frontend static directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h1>Dar Global & Wasalt AI Chatbot Backend Online</h1>")
