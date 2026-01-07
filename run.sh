#!/bin/bash
# Script helper para executar o agente usando uv
# Uso: ./run.sh [agent|api]

case "${1:-agent}" in
  agent)
    echo "🚀 Executando agente..."
    uv run python agent.py
    ;;
  api)
    echo "🌐 Iniciando servidor API na porta 8000..."
    uv run uvicorn agent:app --host 0.0.0.0 --port 8000
    ;;
  *)
    echo "Uso: ./run.sh [agent|api]"
    echo "  agent - Executa o agente diretamente (padrão)"
    echo "  api   - Inicia o servidor API"
    exit 1
    ;;
esac

