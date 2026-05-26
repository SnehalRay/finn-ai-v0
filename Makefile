.PHONY: setup install ingest run-backend run-frontend run test clean help

# -- First-time setup --------------------------------------------------------

setup: install pull-model ingest
	@echo ""
	@echo "Setup complete. Run 'make run' to start Finn."

install:
	@echo "Installing Python dependencies..."
	pip3 install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

pull-model:
	@echo "Pulling Ollama model (llama3.2)..."
	ollama pull llama3.2

ingest:
	@echo "Ingesting knowledge base into ChromaDB..."
	python3 -m knowledge_base.ingest --reset

# -- Running -----------------------------------------------------------------

run:
	@echo "Starting Finn..."
	@echo "  Backend  -> http://localhost:8000"
	@echo "  Frontend -> http://localhost:5173"
	@$(MAKE) run-backend
	@$(MAKE) run-frontend

run-backend:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

run-frontend:
	cd frontend && npm run dev &

# -- Testing -----------------------------------------------------------------

test:
	python3 -m pytest tests/ -v

# -- Cleanup -----------------------------------------------------------------

clean:
	@echo "Stopping servers and wiping local data..."
	pkill -f "uvicorn app.main" 2>/dev/null || true
	pkill -f "vite" 2>/dev/null || true
	rm -rf chroma_db/ finn.db
	@echo "Done."

# -- Help --------------------------------------------------------------------

help:
	@echo ""
	@echo "Finn AI Wellness Bot"
	@echo ""
	@echo "First time:"
	@echo "  make setup        Install deps, pull Ollama model, ingest knowledge base"
	@echo "  make run          Start backend + frontend"
	@echo ""
	@echo "Daily use:"
	@echo "  make run          Start both servers"
	@echo "  make run-backend  Start only the API (port 8000)"
	@echo "  make run-frontend Start only the frontend (port 5173)"
	@echo ""
	@echo "Other:"
	@echo "  make test         Run test suite"
	@echo "  make ingest       Re-ingest knowledge base"
	@echo "  make clean        Stop servers + wipe DB and vector store"
	@echo ""
