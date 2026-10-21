# ðŸ›ï¸ Dar Global & Wasalt AI Assistant


> **Candidate / Developer:** Talha Sadiq
> **ðŸŒ Live Public Demo URL**: [https://listed-supplemental-detail-controlling.trycloudflare.com](https://listed-supplemental-detail-controlling.trycloudflare.com)
> *(Grounded AI Chatbot running live with Docker & OpenRouter free models)*

An enterprise-grade, retrieval-augmented generation (RAG) AI chatbot grounded in verified, publicly available information from **[Dar Global](https://darglobal.co.uk/)** (London-listed luxury real estate developer: LSE: DAR) and **[Wasalt](https://wasalt.sa/en)** (Saudi Arabia's premier PropTech marketplace and e-auction platform).

Powered by free open-weights models through **OpenRouter** (`meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`) and containerized with Docker for seamless one-command deployment.

---

## ðŸŒŸ Key Features


> **Candidate / Developer:** Talha Sadiq
1. **Strictly Grounded RAG Engine**:
   - Hybrid retrieval combining **BM25 term-frequency indexing**, domain entity boosting, and semantic similarity.
   - Grounding on 116,000+ characters of parsed public data covering projects, auctions, financials, and legal compliance.
   - **Clickable Source Citations**: Every generated answer is paired with verified source badges and direct URLs.

2. **Dual-Ecosystem Domain Intelligence**:
   - **Dar Global**: $23B Gross Development Value (GDV), 66% HY 2026 revenue growth, 32-year heritage, presence in 7 countries (Dubai, Qatar, Oman, Spain, London, Maldives, and Riyadh). Branded collaborations with **The Trump Organization**, **Automobili Lamborghini**, **Pagani Automobili**, **Missoni**, and **FENDI Casa**.
   - **Wasalt**: Saudi marketplace listings (villas, apartments, commercial lands) across Riyadh, Jeddah, Dammam, and Khobar; electronic judicial & commercial auctions; secure E-Wallet system; Wafi-certified off-plan projects; and Real Estate General Authority (REGA) **Fal license verification**.
   - **Strategic Synergies**: Compares international high-net-worth trophy investments with domestic Saudi real estate opportunities.

3. **OpenRouter Free Model Tier**:
   - Default: `meta-llama/llama-3.3-70b-instruct:free` (State-of-the-art 70B parameter reasoning).
   - Dynamic Fallback: Automatically falls back to `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.1-8b-instruct:free`, or `qwen/qwen-2.5-coder-32b-instruct:free` if rate limits occur.
   - Real-time token streaming with Server-Sent Events (SSE).

4. **Polished Luxury Interface**:
   - Tailored aesthetic combining dark slate/onyx with champagne gold (`#D4AF37`) and emerald/cyan accents (`#10B981`).
   - Source filtering tabs: *All Ecosystem*, *Dar Global (Luxury)*, and *Wasalt (Saudi PropTech)*.
   - Interactive modal to switch free models or provide an optional personal OpenRouter API key.

5. **Production Containerization**:
   - Dockerized with a lightweight, secure `python:3.11-slim` multi-stage container.
   - Non-root user execution, health checks, and dynamic `$PORT` binding.

---

## ðŸ›¡ï¸ Respect for Access Restrictions (Robots.txt & Policies)


> **Candidate / Developer:** Talha Sadiq
The data collection pipeline strictly abides by the public crawling and AI consumption policies of both platforms:

- **Dar Global (`https://darglobal.co.uk/robots.txt`)**:
  - Allows all standard public pages (`User-agent: *`).
  - Only disallows tracking parameters (`utm_*`, `sfmc_*`, `dealercode`) and sitemap index.
  - Collector only accessed permitted public property pages and press releases with polite rate-limiting.

- **Wasalt (`https://wasalt.sa/robots.txt`)**:
  - Explicitly states: `Allow: /` and `# Note: We're allowing AI access to most areas to support future integrations - no additional restrictions are needed for now.`

> **Candidate / Developer:** Talha Sadiq
  - Disallows internal dynamic search (`Disallow: /search`) and telemetry (`Disallow: /cdn-cgi/rum`).
  - Collector strictly queried permitted static sitemaps, masterplan directories, auction terms, and corporate documentation.

---

## ðŸ“ Repository Structure


> **Candidate / Developer:** Talha Sadiq
```text
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ app.py              # FastAPI server, endpoints, and SSE streaming

> **Candidate / Developer:** Talha Sadiq
â”‚   â”œâ”€â”€ llm_client.py       # OpenRouter client with free models & fallback

> **Candidate / Developer:** Talha Sadiq
â”‚   â”œâ”€â”€ main.py             # Server launcher with dynamic PORT support

> **Candidate / Developer:** Talha Sadiq
â”‚   â””â”€â”€ rag_engine.py       # BM25 & semantic hybrid retrieval engine

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ data/
â”‚   â””â”€â”€ knowledge_base.json # Structured knowledge base (16 documents, 44 chunks)

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ frontend/
â”‚   â”œâ”€â”€ app.js              # Interactive UI logic, SSE reader, citation pills

> **Candidate / Developer:** Talha Sadiq
â”‚   â”œâ”€â”€ index.html          # Modern HTML5 responsive chat workspace

> **Candidate / Developer:** Talha Sadiq
â”‚   â””â”€â”€ style.css           # Luxury styling (glassmorphism, gold/emerald palette)

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ scripts/
â”‚   â””â”€â”€ collect_data.py     # Public scraper & data ingestion pipeline

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_api.py         # FastAPI endpoint integration tests

> **Candidate / Developer:** Talha Sadiq
â”‚   â””â”€â”€ test_rag.py         # Retrieval ranking & scoring tests

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ Dockerfile              # Production Dockerfile

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ docker-compose.yml      # Docker Compose configuration

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ requirements.txt        # Python dependencies

> **Candidate / Developer:** Talha Sadiq
â”œâ”€â”€ .env.example            # Environment variables template

> **Candidate / Developer:** Talha Sadiq
â””â”€â”€ README.md
```

---

## ðŸš€ Quick Start (Local Run)


> **Candidate / Developer:** Talha Sadiq
### 1. Prerequisites

> **Candidate / Developer:** Talha Sadiq
- Python 3.10+ (or Docker)
- Git

### 2. Setup Virtual Environment & Install Dependencies

> **Candidate / Developer:** Talha Sadiq
```bash
python -m venv venv
# On Windows:

> **Candidate / Developer:** Talha Sadiq
.\venv\Scripts\activate
# On Linux/macOS:

> **Candidate / Developer:** Talha Sadiq
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Data Collector (Optional - Pre-collected dataset already included)

> **Candidate / Developer:** Talha Sadiq
```bash
python scripts/collect_data.py
```

### 4. Configure Environment (Optional)

> **Candidate / Developer:** Talha Sadiq
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free OpenRouter API key if desired (`OPENROUTER_API_KEY=sk-or-v1-...`). *Note: Even without an API key, the chatbot features a built-in grounded synthesizer that operates 100% offline!*

### 5. Launch Server

> **Candidate / Developer:** Talha Sadiq
```bash
python backend/main.py
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## ðŸ³ Docker Usage


> **Candidate / Developer:** Talha Sadiq
### Build and Run with Docker

> **Candidate / Developer:** Talha Sadiq
```bash
# Build Docker image

> **Candidate / Developer:** Talha Sadiq
docker build -t dar-wasalt-ai .

# Run container

> **Candidate / Developer:** Talha Sadiq
docker run -d -p 8000:8000 --name dar-wasalt-app dar-wasalt-ai
```

### Or with Docker Compose:

> **Candidate / Developer:** Talha Sadiq
```bash
docker compose up --build
```

Access the application at `http://localhost:8000`.

---

## ðŸŒ Deployment Guide & Live Testing


> **Candidate / Developer:** Talha Sadiq
### Option A: Hugging Face Spaces (Recommended 100% Free Cloud Docker)

> **Candidate / Developer:** Talha Sadiq
1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Choose **Docker** as Space SDK.
3. Push this repository to your Space repository:
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/<SPACE_NAME>
   git push space main
   ```
4. Hugging Face Spaces automatically builds the Dockerfile and provides a public HTTPS URL (`https://<username>-<space_name>.hf.space`).

### Option B: Render.com

> **Candidate / Developer:** Talha Sadiq
1. Create a new **Web Service** on [Render](https://render.com).
2. Select **Docker** environment.
3. Set the Health Check path to `/api/health`.
4. Deploy to receive a public URL (`https://dar-wasalt-ai.onrender.com`).

---

## ðŸ”Œ API Reference


> **Candidate / Developer:** Talha Sadiq
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /api/health` | `GET` | Health check & indexing statistics |
| `GET /api/stats` | `GET` | Documents, chunks, categories, and models |
| `GET /api/models` | `GET` | List of supported free OpenRouter models |
| `POST /api/search` | `POST` | Direct BM25 retrieval over knowledge base |
| `POST /api/chat` | `POST` | Grounded chat completion with citations & streaming |

---

## ðŸ“„ License

> **Candidate / Developer:** Talha Sadiq
MIT License. Developed for technical assessment demonstration.

