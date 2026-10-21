# 🏛️ Dar Global & Wasalt AI Assistant

> **🌐 Live Public Demo URL**: [https://answered-lewis-calibration-experiments.trycloudflare.com](https://answered-lewis-calibration-experiments.trycloudflare.com)
> *(Grounded AI Chatbot running live with Docker & OpenRouter free models)*

An enterprise-grade, retrieval-augmented generation (RAG) AI chatbot grounded in verified, publicly available information from **[Dar Global](https://darglobal.co.uk/)** (London-listed luxury real estate developer: LSE: DAR) and **[Wasalt](https://wasalt.sa/en)** (Saudi Arabia's premier PropTech marketplace and e-auction platform).

Powered by free open-weights models through **OpenRouter** (`meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`) and containerized with Docker for seamless one-command deployment.

---

## 🌟 Key Features

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

## 🛡️ Respect for Access Restrictions (Robots.txt & Policies)

The data collection pipeline strictly abides by the public crawling and AI consumption policies of both platforms:

- **Dar Global (`https://darglobal.co.uk/robots.txt`)**:
  - Allows all standard public pages (`User-agent: *`).
  - Only disallows tracking parameters (`utm_*`, `sfmc_*`, `dealercode`) and sitemap index.
  - Collector only accessed permitted public property pages and press releases with polite rate-limiting.

- **Wasalt (`https://wasalt.sa/robots.txt`)**:
  - Explicitly states: `Allow: /` and `# Note: We're allowing AI access to most areas to support future integrations - no additional restrictions are needed for now.`
  - Disallows internal dynamic search (`Disallow: /search`) and telemetry (`Disallow: /cdn-cgi/rum`).
  - Collector strictly queried permitted static sitemaps, masterplan directories, auction terms, and corporate documentation.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── app.py              # FastAPI server, endpoints, and SSE streaming
│   ├── llm_client.py       # OpenRouter client with free models & fallback
│   ├── main.py             # Server launcher with dynamic PORT support
│   └── rag_engine.py       # BM25 & semantic hybrid retrieval engine
├── data/
│   └── knowledge_base.json # Structured knowledge base (16 documents, 44 chunks)
├── frontend/
│   ├── app.js              # Interactive UI logic, SSE reader, citation pills
│   ├── index.html          # Modern HTML5 responsive chat workspace
│   └── style.css           # Luxury styling (glassmorphism, gold/emerald palette)
├── scripts/
│   └── collect_data.py     # Public scraper & data ingestion pipeline
├── tests/
│   ├── test_api.py         # FastAPI endpoint integration tests
│   └── test_rag.py         # Retrieval ranking & scoring tests
├── Dockerfile              # Production Dockerfile
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md
```

---

## 🚀 Quick Start (Local Run)

### 1. Prerequisites
- Python 3.10+ (or Docker)
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Data Collector (Optional - Pre-collected dataset already included)
```bash
python scripts/collect_data.py
```

### 4. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free OpenRouter API key if desired (`OPENROUTER_API_KEY=sk-or-v1-...`). *Note: Even without an API key, the chatbot features a built-in grounded synthesizer that operates 100% offline!*

### 5. Launch Server
```bash
python backend/main.py
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## 🐳 Docker Usage

### Build and Run with Docker
```bash
# Build Docker image
docker build -t dar-wasalt-ai .

# Run container
docker run -d -p 8000:8000 --name dar-wasalt-app dar-wasalt-ai
```

### Or with Docker Compose:
```bash
docker compose up --build
```

Access the application at `http://localhost:8000`.

---

## 🌐 Deployment Guide & Live Testing

### Option A: Hugging Face Spaces (Recommended 100% Free Cloud Docker)
1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Choose **Docker** as Space SDK.
3. Push this repository to your Space repository:
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/<SPACE_NAME>
   git push space main
   ```
4. Hugging Face Spaces automatically builds the Dockerfile and provides a public HTTPS URL (`https://<username>-<space_name>.hf.space`).

### Option B: Render.com
1. Create a new **Web Service** on [Render](https://render.com).
2. Select **Docker** environment.
3. Set the Health Check path to `/api/health`.
4. Deploy to receive a public URL (`https://dar-wasalt-ai.onrender.com`).

---

## 🔌 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /api/health` | `GET` | Health check & indexing statistics |
| `GET /api/stats` | `GET` | Documents, chunks, categories, and models |
| `GET /api/models` | `GET` | List of supported free OpenRouter models |
| `POST /api/search` | `POST` | Direct BM25 retrieval over knowledge base |
| `POST /api/chat` | `POST` | Grounded chat completion with citations & streaming |

---

## 📄 License
MIT License. Developed for technical assessment demonstration.
