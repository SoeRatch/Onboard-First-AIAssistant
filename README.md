# Onboard-First AI Assistant

An AI-powered onboarding assistant for Company that demonstrates end-to-end AI feature development:  **scraping**, **RAG**, **privacy-aware chat**, and **graceful degradation**.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-gray)

---

## Quick Start

```bash
# 1. Clone and enter directory
cd Onboard-First-AIAssistant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and OPENAI_API_KEY and COMPANY_NAME

# 5. Build Knowledge Base (first time only)
python -m scraper.discover  # 1. Discover relevant URLs
python -m scraper.scrape    # 2. Fetch, extract and chunk content

# 6. Start the server
uvicorn backend.main:app --reload

# 7. Open http://localhost:8000 in your browser
```

---

## Architecture

```
1. **Bootstrap Phase (Manual Run)**
┌─────────────────────────────────────────────────────────────────┐
│                    SCRAPER PIPELINE                             │
│  1. discover.py: Heuristic URL discovery                         │
│  2. scrape.py: Fetch, Cache, Extract, and Chunk                 │
└─────────────────────────────────────────────────────────────────┘
                               │ creates
                               ▼
                        ┌──────────────┐
                        │knowledge.json│
                        └──────────────┘
                               │
2. **Application Phase (Live)**
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Vanilla JS)                         │
│              index.html + style.css + app.js                     │
│         ┌──────────────────┐  ┌──────────────────┐              │
│         │  Onboarding Form │  │  Chat Interface  │              │
│         │  Name/Email/Phone│  │  Real-time Chat  │              │
│         └──────────────────┘  └──────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                               │ REST API
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI + Python)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    API ENDPOINTS                           │  │
│  │  POST /api/chat ──────▶ Chat with AI assistant            │  │
│  │  POST /api/onboard ───▶ Complete onboarding               │  │
│  │  GET  /api/health ────▶ Health check                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    CORE SERVICES                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐   │  │
│  │  │ RAG Engine │  │ PII Masker │  │ Fallback Handler   │   │  │
│  │  │ (ChromaDB) │  │            │  │                    │   │  │
│  │  │            │  │ Mask email │  │ Canned responses   │   │  │
│  │  │ Semantic   │  │ phone, SSN │  │ when API unavail.  │   │  │
│  │  │ search     │  │ before LLM │  │                    │   │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    DATA LAYER                              │  │
│  │  ChromaDB (vectors) │ knowledge.json │ users.json          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  Groq API (Llama 3)      │    │  OpenAI API (GPT-4o)     │
│  (Fast Reranking)        │    │  (Final Answering)       │
└──────────────────────────┘    └──────────────────────────┘
                  (Masked Messages Only)

```

---

## Project Structure

```
Onboard-First-AIAssistant/
├── README.md                 # Project documentation & guide
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore
│
├── scraper/
│   ├── scrape.py             # Main scraper orchestrator
│   ├── content_extractor.py  # BS4 logic for clean text
│   ├── discover.py           # URL discovery
│   ├── knowledge_builder.py  # Semantic chunking & JSON output
│   ├── cache_manager.py      # Local HTML caching
│   ├── utils.py              # User-Agent & robots.txt helpers
│   └── urls.txt              # Seed URLs
│
├── data/
│   ├── knowledge.json        # Generated structured knowledge base (output generated from scraping)
│   ├── users.json            # Generated local user store dynamically (onboarding)
│   ├── chat_history.json     # Generated Encrypted/Masked chat logs
│   └── cache/                # Raw HTML for offline bypass
│
├── backend/
│   ├── main.py               # FastAPI entry point & lifespan
│   ├── rag.py                # Hybrid RAG & VectorStore logic
│   ├── pii.py                # Regex-based PII masking
│   ├── fallback.py           # Keyword search & canned answers
│   └── routers/
│       ├── chat.py           # Chat & Nudge API logic
│       └── onboard.py        # Validation & persistence API
│
├── frontend/
│   ├── index.html            # Dark-themed SPA
│   ├── style.css             # Glassmorphic UI design
│   └── app.js                # Frontend state & API calls
│
├── tests/
│   ├── test_validation.py    # Email/Phone validation logic
│   ├── test_fallback.py      # Offline/Error scenario verification
│   ├── test_nudge.py         # Onboarding prompt frequency logic
│   ├── verify_rag.py         # Manual RAG accuracy check
│   └── verify_api.py         # End-to-end endpoint check

```

---

## Key Design Decisions & Trade-offs

### 1. Hybrid RAG & LLM Strategy
 
 **Decision**: 3-stage pipeline using **Groq (Llama 3)** for speed and **OpenAI (GPT-4o)** for quality.
 1. **Hybrid Retrieval**: BM25 (keywords) + ChromaDB (semantics) fetches top 10.
 2. **Fast Reranking**: Groq/Llama 3 filters to top 4 (ms latency).
 3. **Grounded Answer**: OpenAI generates final response using strict context.

 **Why**: Best balance of cost, speed, and accuracy. Retrieves broadly but filters strictly to prevent hallucinations.

### 2. Scraping: Noise vs. Signal

 **Decision**: Requests + BeautifulSoup with heavy post-processing.
 
 - **Smart Merging**: Chunks < 250 chars are merged to preserve context.
 - **Thresholds**: Tuned similarity to 0.6 to keep related concepts together.
 - **Sitemap Discovery**: Used `sitemap.xml` to find orphaned pages missed by crawlers.
 
 **Trade-off**: `requests` is 10x faster than Playwright but requires custom noise reduction (removing navs/footers) to equal the quality.

### 3. Privacy & Security
 
 **Decision**: Mask PII (email/phone) *before* it leaves the server.
 
 **Why**: Strict compliance. OpenAI is treated as an untrusted third party. `users.json` stays local and gitignored.

### 4. Storage & UX
 
 - **JSON Storage**: Chosen for portability and zero-setup. Meets "local file" requirement but won't scale >1k users.
 - **Gentle Nudge**: Prompts for onboarding only once every 4 messages. Prioritizes user trust over aggressive conversion.


---

## Scraping Approach

### Why Requests + BeautifulSoup?
We chose this over Playwright/Selenium because:
1.  **Minimal Footprint**: No need to install browser binaries (Chromium/Gecko).
2.  **Speed**: 10x faster execution for static content.
3.  **Simplicity**: Easier to allowlist in standard CI/CD environments.

### Noise Reduction Strategy
Early tests showed "Mega Menus" and footers polluting the RAG context. We implemented a strict cleaning pipeline in `scraper/content_extractor.py`:
- **Removed**: `.mega-content`, `.dropdown`, `.mobile-menu`, `.sticky-footer`
- **Result**: `knowledge.json` contains only unique page content, improving retrieval accuracy.

### Execution Workflow

1.  **Discovery (`scraper/discover.py`)**:
    - Scans `sitemap.xml` to find all reachable pages.
    - Filters out irrelevancies (PDFs, login pages).
    - **Output**: `scraper/urls.txt`

2.  **Intelligent Fetching (`scraper/scrape.py`)**:
    - **Caching**: Checks `data/cache/*.html` first. If missing, fetches and saves raw HTML.
    - **Benefit**: Prevents redundant network requests and speeds up re-runs.

3.  **Extraction & Cleaning**:
    - Loads HTML from cache.
    - Strips "Mega Menus", navbars, and footers (Noise Reduction).
    - **Output**: Clean, main-body text.

4.  **Semantic Chunking**:
    - Splits text into sentences.
    - Merges small fragments (<250 chars) to preserve context.
    - Uses strict `1500` char limit to fit RAG context window.

5.  **Knowledge Building**:
    - Compiles everything into structured JSON.
    - **Output**: `data/knowledge.json` (Ready for RAG)

### Running the Scraper

```bash
python scraper/scrape.py
```

Output: `data/knowledge.json` (contains page info and semantic chunks)

---

## Threat Model: PII Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         PII FLOW                                 │
│                                                                  │
│  User types: "My email is john@example.com"                     │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ FRONTEND: Sends raw message to backend                      ││
│  │ (PII travels over HTTPS to OUR server only)                 ││
│  └─────────────────────────────────────────────────────────────┘│
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ BACKEND: PII Masker intercepts                              ││
│  │ "My email is john@example.com" → "My email is [REDACTED]"   ││
│  └─────────────────────────────────────────────────────────────┘│
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ EXTERNAL APIs: Only see masked messages                      ││
│  │ "My email is [EMAIL_REDACTED]"                              ││
│  │ ⚠️ NEVER receive actual PII                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ LOCAL STORAGE: Original PII stored in users.json            ││
│  │ Never leaves the server                                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Risk Mitigations

| Threat | Mitigation |
|--------|------------|
| **PII Leakage** | All PII masked (email/phone) before API call. Verified in `backend/pii.py`. |
| **Data Breach** | User data stored locally in `users.json` (gitignored). Production would use encrypted DB. |
| **Prompt Injection** | System prompt explicitly constrains LLM to "only use provided context". |
| **Hallucination** | Hybrid RAG pipeline prioritizes grounded answers; returns "I don't know" if context missing. |

---

## Failure Modes & Graceful Degradation

| Scenario | Detection | Fallback Behavior |
|----------|-----------|-------------------|
| **API timeout** | 10s timeout | "I'm having connection issues. You can still complete onboarding via the form." |
| **API error** | 5xx/4xx response | Same as above, plus simple FAQ matching |
| **Scraper fails** | Exception caught | Use cached data, log for investigation |
| **Unknown question** | No relevant KB match | "I don't have information about that specific topic. I can help with X, Y, Z." |
| **ChromaDB unavailable** | Exception | Fall back to keyword matching in knowledge.json |

---

## Running Tests

```bash
# Run all tests
cd Onboard-First_AIAssistant
pytest tests/ -v

# Run specific test file
pytest tests/test_validation.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=term-missing
```

### Test Coverage

- **test_validation.py**: Email/phone format validation (valid/invalid cases)
- **test_fallback.py**: Unknown questions, API errors, safe responses
- **test_nudge.py**: Nudge frequency, message content, non-annoying behavior
- **verify_rag.py**: Script to verify RAG engine initialization and retrieval manually.

### Manual Verification
Run `python tests/verify_rag.py` to check if knowledge base has been indexed correctly and returns relevant results.

---

## Autonomy Prompts

### What did you not build and why?

1. **User authentication** - Not required for demo; would add complexity without value for the assignment scope
2. **Database (SQLite/Postgres)** - JSON files are simpler and meet the "local knowledge file" requirement
3. **Email/SMS notifications** - Would require third-party services and leak PII
4. **Admin dashboard** - Not part of the core user journey
5. **Rate limiting** - Would need Redis/similar; overkill for demo

### How does your system behave if scraping fails or LLM/API is down?

1. **Scraping fails**: 
   - Uses cached HTML from previous successful scrapes
   - Logs the failure for investigation
   - App continues with stale but functional knowledge base

2. **LLM/API down**:
   - Returns canned responses for common questions (services, about, tax)
   - Prompts user to try again or complete onboarding via form
   - All core functionality (onboarding form) remains operational

### Where could this be gamed or produce unsafe answers?

1. **Prompt injection**: User could try to manipulate the LLM via crafted messages
   - *Mitigation*: System prompt explicitly constrains responses to KB content
   
2. **Fake onboarding**: User could submit fake email/phone
   - *Mitigation*: Format validation; would need OTP for real verification
   
3. **Scraping stale data**: Knowledge base could become outdated
   - *Mitigation*: Timestamp on scrape; scheduled re-scraping in production

4. **Hallucination despite rules**: LLM might occasionally make up facts
   - *Mitigation*: Strong grounding prompt; source citations in response

### How would you extend this to support OTP verification without leaking PII to third parties?

```
┌─────────────────────────────────────────────────────────────────┐
│                    OTP VERIFICATION FLOW                         │
│                                                                  │
│  1. User submits phone number to OUR backend                    │
│       │                                                          │
│       ▼                                                          │
│  2. Backend generates OTP, stores hash locally                  │
│       │                                                          │
│       ▼                                                          │
│  3. Backend uses Twilio/similar with OUR account                │
│     (Twilio only sees phone number - not linked to user data)   │
│       │                                                          │
│       ▼                                                          │
│  4. User receives SMS, enters OTP in frontend                   │
│       │                                                          │
│       ▼                                                          │
│  5. Backend verifies OTP hash matches                           │
│     ✅ Phone verified, no PII leaked to third party             │
└─────────────────────────────────────────────────────────────────┘
```

Key points:
- Generate OTP server-side, don't use external OTP services
- Only phone number sent to SMS gateway (minimal PII)
- Never send name/email alongside phone to external service
- Store only hashed OTP, not plaintext

---

## License

MIT License - Built for screening assessment.