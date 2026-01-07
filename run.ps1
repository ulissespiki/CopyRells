# Script helper para executar o agente usando uv (PowerShell)
# Uso: .\run.ps1 [agent|api]

param(
    [Parameter(Position=0)]
    [ValidateSet("agent", "api")]
    [string]$Mode = "agent"
)

switch ($Mode) {
    "agent" {
        Write-Host "🚀 Executando agente..." -ForegroundColor Green
        uv run python agent.py
    }
    "api" {
        Write-Host "🌐 Iniciando servidor API na porta 8000..." -ForegroundColor Cyan
        uv run uvicorn agent:app --host 0.0.0.0 --port 8000
    }
    default {
        Write-Host "Uso: .\run.ps1 [agent|api]" -ForegroundColor Yellow
        Write-Host "  agent - Executa o agente diretamente (padrão)"
        Write-Host "  api   - Inicia o servidor API"
        exit 1
    }
}

