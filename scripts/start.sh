#!/bin/bash
set -e

# Finn AI Wellness Bot — one-command setup and launch
# Usage: bash scripts/start.sh

# -- Prerequisites check -----------------------------------------------------

check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "Error: '$1' is not installed. $2"
        exit 1
    fi
}

check_command python3  "Install Python 3.11+ from https://python.org"
check_command pip3     "Install pip: https://pip.pypa.io"
check_command ollama   "Install Ollama from https://ollama.com"
check_command npm      "Install Node.js from https://nodejs.org"

# -- Install dependencies ----------------------------------------------------

echo "Installing Python dependencies..."
pip3 install -r requirements.txt -q

echo "Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

# -- Pull model if not already available -------------------------------------

if ! ollama list | grep -q "llama3.2"; then
    echo "Pulling llama3.2 model (this may take a few minutes)..."
    ollama pull llama3.2
else
    echo "llama3.2 already available."
fi

# -- Ingest knowledge base ---------------------------------------------------

if [ ! -d "chroma_db" ]; then
    echo "Building knowledge base..."
    python3 -m knowledge_base.ingest --reset
else
    echo "Knowledge base already built. Skipping ingest. (Run 'make ingest' to rebuild.)"
fi

# -- Start servers -----------------------------------------------------------

echo ""
echo "Starting Finn..."

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Finn is running:"
echo "  Backend  -> http://localhost:8000"
echo "  Frontend -> http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop."

# -- Graceful shutdown -------------------------------------------------------

trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
