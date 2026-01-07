"""
Agente de Copywriting para Influenciadores Digitais
Usa OpenAI, Tavily para pesquisa web e PostgreSQL para histórico

Estrutura:
1. Importações das bibliotecas do Agno
2. Configuração do banco de dados PostgreSQL
3. Criação do agente com ferramentas e configurações
4. Configuração do AgentOS para servir como API
5. Exemplo de uso local
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Importações do framework Agno
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.tavily import TavilyTools
from agno.db.postgres import PostgresDb
from agno.os import AgentOS

from transcription_reader import get_creator_transcriptions, list_available_creators

# ============================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================
# PostgreSQL para armazenar histórico de sessões
# Formato DATABASE_URL: postgresql://usuario:senha@host:porta/nome_banco
db = PostgresDb(db_url=os.getenv("DATABASE_URL"))

# ============================================
# CRIAÇÃO DO AGENTE
# ============================================
# IMPORTANTE: Criar o agente uma vez e reutilizar (não criar em loops)
# Isso garante melhor performance e reutilização de recursos
agent = Agent(
    # Modelo OpenAI para geração de conteúdo inteligente
    id="copywriter_modelador",
    model=OpenAIChat(id="gpt-5.2", service_tier='flex'),
    name="Copywriter Modelador",
    description="Copywriter que pesquisa assunto na web e modela alguns influencer da base de dados para criar conteúdo",
    
    # Ferramenta de pesquisa web Tavily
    # Permite ao agente buscar informações atualizadas na internet
    tools=[
            TavilyTools(),
            list_available_creators,
            get_creator_transcriptions
        ],
    
    # Banco de dados para persistir histórico de conversações
    db=db,
    
    # ID do usuário para isolar sessões
    # Em produção, use IDs únicos por cliente/influenciador
    user_id="influencer-copywriter",
    
    # Adiciona histórico ao contexto para manter continuidade na conversa
    add_history_to_context=True,
    
    # Número de interações anteriores a incluir no contexto
    # Mantém memória das últimas 10 conversas
    num_history_runs=10,
    # If True, the agent creates/updates user memories at the end of runs
    enable_user_memories=True,
    
    # Instruções específicas para o domínio de copywriting
    instructions=open("prompts/copywriter_modelador.md").read(),
    
    # Formato de saída em Markdown para melhor legibilidade
    markdown=True,
    debug_mode=False
)

# ============================================
# CONFIGURAÇÃO DO AGENTOS
# ============================================
# AgentOS serve o agente como API REST pronta para produção
# Gerencia: rotas HTTP, autenticação, escalabilidade, logs
agent_os = AgentOS(
    agents=[agent],  # Lista de agentes disponíveis
    name="Agente Copywriter Modelador - API",
    description="API - Copywriter que pesquisa assunto na web e modela alguns influencer da base de dados para criar conteudo",
    version="1.0.0",
)

# Aplicação FastAPI pronta para deploy
# Acessível via HTTP após iniciar o servidor
app = agent_os.get_app()

# ============================================
# EXECUÇÃO LOCAL (TESTES)
# ============================================
if __name__ == "__main__":
    # Exemplo de uso direto do agente
    # Em produção, use a API HTTP do AgentOS
    # response = agent.run(
    #     "Crie um copy para Instagram sobre lançamento de curso de marketing digital"
    # )
    # agent.print_response(response.content, stream=True)
    agent_os.serve(app="agent:app", reload=True, host="192.168.0.13")

