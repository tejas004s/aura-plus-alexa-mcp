#!/usr/bin/env bash
# run.sh - One-command launcher for Aura+ (Alexa+ MCP Server & Web Simulator)

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "  🌟 Launching Aura+ (Alexa+ Autonomous Concierge & MCP Server) 🌟"
echo "================================================================="

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment .venv not found. Creating..."
    python3 -m virtualenv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

export PYTHONPATH=.

# Run test suite verification
echo "Running protocol and skill verification tests..."
pytest -q tests/

echo ""
echo "🚀 Starting Aura+ Server on http://localhost:8000"
echo "   - Alexa+ Simulated Web UI: http://localhost:8000"
echo "   - Streamable HTTP MCP SSE: http://localhost:8000/mcp/sse"
echo "   - MCP Message Endpoint:   http://localhost:8000/mcp/message"
echo "================================================================="
echo "Press Ctrl+C to stop."

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
