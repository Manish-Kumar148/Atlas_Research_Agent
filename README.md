# ⬡ Atlas Research Agent

An autonomous multi-agent AI research platform. Enter a topic, and a pipeline of 7 specialized agents researches it end-to-end — searching the web, extracting insights, persisting memory, reflecting on completeness, and generating a structured report.

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                  │
│                                                      │
│  🎯 Task Understanding → 🗺️ Planning                 │
│       → 🔍 Web Research (Tavily)                     │
│       → ⚙️  Knowledge Extraction                     │
│       → 🧠 Memory Agent (ChromaDB + Redis)           │
│       → 🪞 Reflection (re-search if < 85%)           │
│       → 📊 Report Generation                         │
└─────────────────────────────────────────────────────┘
    │
    ▼ SSE stream
┌─────────────────────────────────────────────────────┐
│              Next.js 15 Frontend                     │
│  Live Feed │ Agent Pipeline │ Memory │ Sources       │
│                   Report Viewer                      │
└─────────────────────────────────────────────────────┘
```

**Backend:** FastAPI + LangGraph + Anthropic Claude + Tavily  
**Memory:** ChromaDB (vector) + Redis (session) + PostgreSQL (persistence)  
**Frontend:** Next.js 15 + TypeScript + TailwindCSS + Zustand

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- API keys: [Anthropic](https://console.anthropic.com) and [Tavily](https://tavily.com)

### 2. Clone and configure

```bash
git clone <repo-url> atlas-research
cd atlas-research

cp .env.example backend/.env
# Edit backend/.env and fill in:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TAVILY_API_KEY=tvly-...
```

### 3. Run everything

```bash
bash scripts/dev.sh
```

This starts Docker services, installs deps, and launches frontend + backend.

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:3000        |
| Backend   | http://localhost:8000        |
| API Docs  | http://localhost:8000/docs   |
| Adminer   | http://localhost:8080        |

---

## Manual Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env  # fill in keys
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Infrastructure (Docker)

```bash
docker compose up -d postgres redis chromadb
```

---

## API Reference

### POST `/research/start`
Start a research session.
```json
{ "topic": "AI agents for ecommerce automation", "workspace_id": null }
```
Returns: `{ "session_id": "uuid" }`

### GET `/research/stream/{session_id}`
SSE stream of agent events. Each event:
```json
{
  "agent_id": "web_research",
  "event": "completed",
  "timestamp": "2025-01-01T00:00:00Z",
  "summary": "Executed 6 searches, 28 unique sources collected.",
  "tool_calls": ["tavily.search(...)"],
  "data": { "source_count": 28, "sources": [...] }
}
```

### GET `/research/report/{session_id}`
Fetch the final structured report.

### POST `/memory/query`
Semantic search over stored research.
```json
{ "query": "LLM agent limitations", "top_k": 5 }
```

### GET/POST `/workspaces/`
Workspace CRUD.

---

## Project Structure

```
atlas-research/
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Settings
│   ├── agents/
│   │   ├── graph.py               # LangGraph orchestration
│   │   ├── state.py               # ResearchState TypedDict
│   │   └── nodes/                 # 7 agent implementations
│   ├── services/
│   │   ├── claude_client.py       # Anthropic wrapper
│   │   ├── chroma_service.py      # ChromaDB operations
│   │   ├── redis_service.py       # Redis session state
│   │   └── postgres_service.py    # DB CRUD
│   ├── api/routes/                # FastAPI routers
│   └── models/                    # SQLAlchemy + Pydantic
│
├── frontend/
│   ├── app/                       # Next.js App Router
│   ├── components/                # UI components
│   ├── store/researchStore.ts     # Zustand state
│   ├── lib/streamClient.ts        # SSE consumer
│   └── types/index.ts             # TypeScript types
│
├── docker-compose.yml
├── .env.example
└── scripts/dev.sh
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `ANTHROPIC_MODEL` | Model (default: claude-sonnet-4-20250514) |
| `TAVILY_API_KEY` | Tavily search API key |
| `DATABASE_URL` | PostgreSQL async URL |
| `REDIS_URL` | Redis connection URL |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB location |
| `FRONTEND_URL` | For CORS (default: http://localhost:3000) |

---

## Deployment

### Backend → Railway / Render
```bash
# Set all env vars in dashboard
# Start command:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend → Vercel
```bash
cd frontend
vercel deploy
# Set NEXT_PUBLIC_BACKEND_URL=https://your-backend.railway.app
```

### Database → Supabase
Set `DATABASE_URL` to your Supabase PostgreSQL connection string.

---

## Example Research Topics

- *"Browser agents for ecommerce automation"*
- *"LLM inference optimization techniques 2025"*
- *"Quantum computing applications in drug discovery"*
- *"Competitive landscape of AI coding assistants"*
- *"Autonomous vehicle sensor fusion architectures"*
