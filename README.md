# Agente de Copywriting para Influenciadores

Agente inteligente para criação de copywriting usando Agno Framework, OpenAI, Tavily e PostgreSQL.

## Funcionalidades

- ✅ Geração de copywriting personalizado
- ✅ Pesquisa web em tempo real (Tavily)
- ✅ Histórico de sessões no PostgreSQL
- ✅ API REST via AgentOS
- ✅ Frontend Streamlit com interface de chat interativa
- ✅ Streaming de respostas em tempo real
- ✅ Gerenciamento de múltiplas sessões de conversa
- ✅ Contexto de conversação mantido
- ✅ Gerenciamento de pacotes com `uv` (ultra-rápido)

## Pré-requisitos

- Python 3.10 ou superior
- [uv](https://github.com/astral-sh/uv) - Gerenciador de pacotes Python (instalação rápida: `pip install uv` ou `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Instalação

### 1. Instalar o uv (se ainda não tiver)

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip
pip install uv
```

### 2. Sincronizar dependências

O `uv` gerencia automaticamente o ambiente virtual e as dependências:

```bash
# Sincroniza todas as dependências do pyproject.toml
uv sync

# Ou instala apenas as dependências (sem ambiente virtual)
uv pip install -e .
```

**Nota:** O `uv sync` cria automaticamente um ambiente virtual em `.venv` e instala todas as dependências listadas no `pyproject.toml` e lockadas no `uv.lock`.

### 3. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto:
```env
OPENAI_API_KEY=sua_chave_openai_aqui
TAVILY_API_KEY=sua_chave_tavily_aqui
DATABASE_URL=postgresql://usuario:senha@localhost:5432/copyrells_db
```

### 4. Crie o banco de dados PostgreSQL:
```sql
CREATE DATABASE copyrells_db;
```

## Uso

### Modo API (AgentOS) - Recomendado para Produção

Para servir o agente como API REST usando `uv`:

```bash
# Usando uv run (recomendado - gerencia ambiente automaticamente)
uv run uvicorn agent:app --host 0.0.0.0 --port 8000

# Ou usando o ambiente virtual do uv
uv run python -m uvicorn agent:app --host 0.0.0.0 --port 8000
```

O agente estará disponível em: `http://localhost:8000`

### Frontend Streamlit - Interface de Chat

Para usar o frontend Streamlit, primeiro inicie a API (veja seção acima) e depois inicie o frontend:

```bash
# Inicia o frontend Streamlit
uv run streamlit run frontend_streamlit.py

# Ou usando o ambiente virtual
uv run python -m streamlit run frontend_streamlit.py
```

O frontend estará disponível em: `http://localhost:8501`

#### Funcionalidades do Frontend:

- 💬 **Chat interativo** com o agente de copywriting
- 🔄 **Streaming de respostas** em tempo real
- 💾 **Gerenciamento de sessões** - criar, selecionar e deletar sessões
- 📜 **Histórico completo** - visualiza todas as mensagens trocadas
- 🤖 **Seleção de agente** - escolha qual agente conversar (preparado para múltiplos agentes)
- 🔌 **Verificação de conexão** com a API

#### Configuração do Frontend:

O frontend se conecta à API através da variável de ambiente `AGENTOS_API_URL`. 
Por padrão, usa `http://localhost:8000`. Para alterar, adicione no arquivo `.env`:

```env
AGENTOS_API_URL=http://localhost:8000
USER_ID=influencer-copywriter
```

### Uso Direto (Testes)

Para testar o agente diretamente sem API:

```bash
# Usando uv run (recomendado)
uv run python agent.py

# Ou usando o ambiente virtual do uv manualmente
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows
python agent.py
```

### Scripts Helper (Opcional)

Scripts auxiliares para facilitar a execução:

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh agent    # Executa o agente
./run.sh api      # Inicia a API
```

**Windows (PowerShell):**
```powershell
.\run.ps1 agent   # Executa o agente
.\run.ps1 api     # Inicia a API
```

### Comandos Úteis do uv

```bash
# Adicionar nova dependência
uv add nome-do-pacote

# Adicionar dependência de desenvolvimento
uv add --group dev nome-do-pacote

# Remover dependência
uv remove nome-do-pacote

# Atualizar dependências
uv sync --upgrade

# Ver dependências instaladas
uv pip list

# Executar script Python
uv run python script.py

# Executar comando do projeto
uv run nome-do-comando

# Sincronizar ambiente (cria/atualiza .venv)
uv sync
```

## Estrutura do Código

- `agent.py`: Código principal do agente e API AgentOS
- `frontend_streamlit.py`: Frontend Streamlit com interface de chat
- `transcription_reader.py`: Leitor de transcrições de vídeos
- `pyproject.toml`: Configuração do projeto e dependências (padrão moderno)
- `uv.lock`: Lock file do uv com versões exatas das dependências (deve ser commitado)
- `requirements.txt`: Dependências (mantido para compatibilidade)
- `run.sh` / `run.ps1`: Scripts helper para executar o projeto (opcional)
- `.gitignore`: Arquivos ignorados pelo Git
- `config_example.txt`: Exemplo de configuração
- `prompts/`: Prompts do agente

## Gerenciamento de Dependências com uv

### Por que usar uv?

- 🚀 **10-100x mais rápido** que pip
- 🔒 **Lock file determinístico** (`uv.lock`)
- 🎯 **Gerenciamento automático** do ambiente virtual
- 📦 **Compatível com pip** e padrões Python modernos

### Comandos Principais

```bash
# Sincronizar ambiente e dependências
uv sync

# Adicionar nova dependência
uv add pacote-nome

# Atualizar todas as dependências
uv sync --upgrade

# Executar aplicação
uv run python agent.py

# Executar servidor API
uv run uvicorn agent:app --host 0.0.0.0 --port 8000
```

## Observações

- O agente é criado uma vez e reutilizado (boa prática de performance)
- O histórico é mantido automaticamente pelo PostgreSQL
- O agente pesquisa automaticamente antes de criar copy
- O `uv` gerencia automaticamente o ambiente virtual (`.venv`)
- O arquivo `uv.lock` garante dependências consistentes entre ambientes

