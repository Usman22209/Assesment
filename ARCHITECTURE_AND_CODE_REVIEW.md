# Assessment: Dar Global & Wasalt AI Chatbot - Code Review & Architecture Document

> **Candidate / Developer:** Usman Shafiq  
> **Position / Role:** AI / Full-Stack Engineer  
> **Live Public Application:** [https://listed-supplemental-detail-controlling.trycloudflare.com](https://listed-supplemental-detail-controlling.trycloudflare.com)  
> **Repository:** [https://github.com/Usman22209/Assesment](https://github.com/Usman22209/Assesment)  

---

## 📋 Table of Contents
1. [RAG Architecture & Anti-Hallucination Design](#1-rag-architecture--anti-hallucination-design)
2. [Multi-Tier LLM Orchestration & Resilience](#2-multi-tier-llm-orchestration--resilience)
3. [Containerization & 24/7 Cloud Deployment](#3-containerization--247-cloud-deployment)
4. [Robots.txt & Ethical Web Scraping Architecture](#4-robotstxt--ethical-web-scraping-architecture)
5. [Code Review Best Practices & Security Standards](#5-code-review-best-practices--security-standards)

---

## 1. RAG Architecture & Anti-Hallucination Design

The application implements a production-grade, retrieval-augmented generation (RAG) pipeline designed specifically for real estate intelligence with zero tolerance for hallucinations:

```
[User Query] -> [FastAPI /api/chat] -> [Hybrid BM25 Retriever] -> [Ranked Chunks & Citations]
                                                                        |
[UI Citation Cards] <- [Synthesized Response] <- [Strict Grounding Prompt + OpenRouter LLM]
```

### Key Architectural Decisions:
1. **Hybrid BM25 + Domain Keyword Boosting:** Standard dense embeddings frequently dilute domain-specific jargon (e.g. *Wafi, Fal, GDV, Pagani, off-plan, Simaisma*). The BM25 engine calculates exact term frequency-inverse document frequency over luxury real estate terminology to ensure 100% relevant document matches.
2. **Deterministic Anti-Hallucination Guardrails:** System prompts enforce answering strictly from retrieved context. If a user asks a question outside the indexed knowledge base, the model explicitly acknowledges the limitation and directs the user to official developer contact channels rather than confabulating.
3. **Traceable Attribution:** Every generated sentence is backed by interactive citation badges pointing to canonical source URLs, document IDs, and exact publication dates.

---

## 2. Multi-Tier LLM Orchestration & Resilience

To satisfy the requirement of using free models through OpenRouter while ensuring 100% service availability:

1. **Primary Model:** `minimax/minimax-m3.1-flash:free` (ultra-fast TTFT and streaming tokens).
2. **Secondary Fallback:** `poolside/laguna-s-2.1:free` (concise reasoning and low latency).
3. **Tertiary Fallbacks:** `nvidia/nemotron-3-ultra-550b-a55b:free` (deep reasoning) and `liquid/lfm-2.5-2.6b:free`.
4. **Key Sanitization:** User tokens are automatically normalized, stripping `Bearer ` prefixes and whitespace to prevent authorization errors.
5. **Offline Extractive Fallback:** If the OpenRouter public free tier is entirely rate-limited upstream, a deterministic extractive synthesis layer generates a structured answer grounded in top-ranked chunks without dropping user connections.

---

## 3. Containerization & 24/7 Cloud Deployment

1. **Multi-Stage Docker Architecture:**
   - **Base Image:** `python:3.11-slim` with an unprivileged system user (`appuser:appgroup`).
   - **Dynamic `$PORT` Binding:** Supports serverless platforms (AWS ECS, GCP Cloud Run, Render) and container orchestrators.
   - **Health Checks:** Built-in `HEALTHCHECK` pinging `/api/health` every 30 seconds.
2. **Production Cloud Deployment:**
   - Deployed on an isolated Linux VPS with 24/7 uptime managed by **PM2**.
   - **Zero IP Exposure:** Outbound Cloudflare Tunnel forwards public HTTPS traffic directly to local service ports, keeping backend IP addresses and server infrastructure 100% invisible to the internet.

---

## 4. Robots.txt & Ethical Web Scraping Architecture

Data collection (`scripts/collect_data.py`) strictly adheres to web scraping ethics and platform rules:

- **Dar Global (`darglobal.co.uk`):** Respected disallow rules on tracking parameters (`*?*utm_*`, `*?*sfmc_*`) and extracted only publicly indexable landing pages with polite request throttling.
- **Wasalt (`wasalt.sa`):** Wasalt explicitly permits AI access (`Allow: /`). The scraper strictly avoided dynamic search queries (`/search`) and telemetry (`/cdn-cgi/rum`), capturing static documentation, auction guidelines, and regulatory frameworks.

---

## 5. Code Review Best Practices & Security Standards

1. **Input Validation:** Pydantic schemas validate all incoming JSON payloads, rejecting malformed requests prior to RAG execution.
2. **Streaming Safety:** Server-Sent Events (SSE) connections are wrapped with disconnect monitors to prevent socket leaks during client drops.
3. **Secret Hygiene:** Zero hardcoded API keys. Environment credentials are loaded strictly via `.env` with complete `.env.example` templates provided.
4. **Automated Test Coverage:** Includes unit tests for retrieval accuracy (`tests/test_rag.py`) and integration tests for API endpoints (`tests/test_api.py`).
