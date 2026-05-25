#!/bin/bash
set -e

echo ""
echo "  ⬡  Atlas Research Agent"
echo "  ─────────────────────────────"
echo ""

# Check .env exists
if [ ! -f "backend/.env" ]; then
  echo "  → Copying .env.example to backend/.env"
  cp .env.example backend/.env
  echo "  ⚠  Edit backend/.env and add your API keys before running!"
  echo ""
fi

# Start infrastructure
echo "  → Starting Docker services (Postgres, Redis, ChromaDB)…"
docker compose up -d postgres redis chromadb

echo "  → Waiting for services to be healthy…"
sleep 6

# Backend
echo "  → Installing backend dependencies…"
cd backend
pip install -r requirements.txt -q
echo "  → Starting FastAPI backend on :8000"
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend
echo "  → Installing frontend dependencies…"
cd frontend
npm install --silent
echo "  → Starting Next.js frontend on :3000"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "  ✓  Atlas Research Agent is running!"
echo ""
echo "     Frontend  →  http://localhost:3000"
echo "     Backend   →  http://localhost:8000"
echo "     API Docs  →  http://localhost:8000/docs"
echo "     Adminer   →  http://localhost:8080"
echo ""
echo "  Press Ctrl+C to stop all services."
echo ""

trap "echo '  → Stopping…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose stop; exit 0" INT TERM
wait
