# Guia Rápido - uv

Este projeto usa [uv](https://github.com/astral-sh/uv), um gerenciador de pacotes Python ultra-rápido.

## Instalação Rápida

### 1. Instalar o uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip
pip install uv
```

### 2. Sincronizar Dependências

```bash
uv sync
```

Isso cria automaticamente o ambiente virtual `.venv` e instala todas as dependências.

## Comandos Principais

### Executar Aplicação

```bash
# Executar agente diretamente
uv run python agent.py

# Iniciar servidor API
uv run uvicorn agent:app --host 0.0.0.0 --port 8000
```

### Gerenciar Dependências

```bash
# Adicionar nova dependência
uv add nome-do-pacote

# Adicionar dependência de desenvolvimento
uv add --group dev nome-do-pacote

# Remover dependência
uv remove nome-do-pacote

# Atualizar todas as dependências
uv sync --upgrade
```

### Outros Comandos Úteis

```bash
# Verificar status do ambiente
uv sync --check

# Listar dependências instaladas
uv pip list

# Executar qualquer comando Python
uv run python script.py
```

## Vantagens do uv

- 🚀 **10-100x mais rápido** que pip
- 🔒 **Lock file determinístico** (`uv.lock`)
- 🎯 **Gerenciamento automático** do ambiente virtual
- 📦 **Compatível com pip** e padrões Python modernos
- 🔄 **Sincronização inteligente** de dependências

## Notas Importantes

- O `uv.lock` **deve ser commitado** no repositório
- O ambiente virtual `.venv` é criado automaticamente pelo `uv`
- Use `uv run` para executar comandos no ambiente do projeto
- O `uv sync` garante que o ambiente está sempre sincronizado com `pyproject.toml`

