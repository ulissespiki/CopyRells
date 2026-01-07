"""
Frontend Streamlit para o Agente de Copywriting
Conecta-se à API do AgentOS e fornece interface de chat interativa
"""

import os
import json
import time
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import streamlit as st
import requests
from dotenv import load_dotenv

# Configura encoding UTF-8 para garantir acentuação correta
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    import io
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Carrega variáveis de ambiente
load_dotenv()

# ============================================
# CONFIGURAÇÃO
# ============================================
# URL da API AgentOS (padrão: http://localhost:8000)
API_BASE_URL = os.getenv("AGENTOS_API_URL", "http://localhost:8000")
USER_ID = os.getenv("USER_ID", "influencer-copywriter")

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def get_agents() -> List[Dict]:
    """Busca lista de agentes disponíveis na API"""
    try:
        response = requests.get(f"{API_BASE_URL}/agents", timeout=5)
        if response.status_code == 200:
            agents = response.json()
            # Garante que seja uma lista
            if isinstance(agents, list):
                return agents
            elif isinstance(agents, dict) and "data" in agents:
                return agents["data"]
            return []
        return []
    except requests.exceptions.ConnectionError:
        # Não mostra erro se a API não estiver rodando (evita spam de erros)
        return []
    except Exception as e:
        # Apenas mostra erro se for algo inesperado
        if "error" not in st.session_state or not st.session_state.error:
            st.session_state.error = True
        return []


def get_sessions(agent_id: str, db_id: Optional[str] = None) -> List[Dict]:
    """Busca sessões disponíveis para um agente"""
    try:
        params = {
            "type": "agent",
            "component_id": agent_id,
        }
        if db_id:
            params["db_id"] = db_id
        
        response = requests.get(
            f"{API_BASE_URL}/sessions",
            params=params,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        elif response.status_code == 404:
            return []
        return []
    except Exception as e:
        st.error(f"Erro ao buscar sessões: {str(e)}")
        return []


def process_content(content) -> str:
    """Processa conteúdo que pode ser string, objeto ou array"""
    if content is None:
        return ""
    
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        # Se for array, procura por itens do tipo 'text'
        text_items = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
        if text_items:
            return " ".join(text_items)
        # Se não encontrar, converte tudo para string
        return " ".join(str(item) for item in content)
    
    if isinstance(content, dict):
        # Se for objeto, tenta extrair campos comuns primeiro
        # Muitas APIs retornam conteúdo em campos como 'content', 'text', 'message', 'output'
        if "content" in content:
            result = process_content(content["content"])
            if result:
                return result
        if "text" in content:
            result = process_content(content["text"])
            if result:
                return result
        if "message" in content:
            result = process_content(content["message"])
            if result:
                return result
        if "output" in content:
            result = process_content(content["output"])
            if result:
                return result
        
        # Se não encontrou campos comuns, verifica se é um objeto vazio
        if not content:
            return ""
        
        # Se ainda tem conteúdo, converte para JSON formatado
        return json.dumps(content, ensure_ascii=False, indent=2)
    
    return str(content)


def get_session_history(session_id: str, agent_id: str, db_id: Optional[str] = None) -> List[Dict]:
    """Busca histórico de mensagens de uma sessão"""
    try:
        params = {
            "type": "agent",
        }
        if db_id:
            params["db_id"] = db_id
        
        response = requests.get(
            f"{API_BASE_URL}/sessions/{session_id}/runs",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            # A API pode retornar diretamente um array ou dentro de "data"
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Pode estar em "data" ou "runs"
                result = data.get("data", [])
                if not result:
                    result = data.get("runs", [])
                return result
        elif response.status_code == 404:
            return []
        return []
    except requests.exceptions.ConnectionError:
        return []
    except Exception as e:
        # Não mostra erro aqui, deixa o código chamador tratar
        return []


def create_smart_summary(text: str, max_length: int = 30) -> str:
    """Cria um resumo inteligente do texto, extraindo palavras-chave e frases principais"""
    if not text or not text.strip():
        return "Sessão"
    
    # Remove quebras de linha e espaços extras
    text = " ".join(text.split())
    
    # Se o texto já é curto, retorna direto
    if len(text) <= max_length:
        return text
    
    # Remove pontuação no final para melhor corte
    text = text.rstrip('.,!?;:')
    
    # Tenta encontrar uma frase completa que caiba
    sentences = text.split('.')
    if sentences:
        # Pega a primeira frase se couber
        first_sentence = sentences[0].strip()
        if len(first_sentence) <= max_length:
            return first_sentence
    
    # Se não couber, tenta pegar as primeiras palavras importantes
    words = text.split()
    
    # Remove palavras muito curtas e comuns (stop words básicas)
    stop_words = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos', 
                  'em', 'na', 'no', 'nas', 'nos', 'para', 'com', 'por', 'que', 'é'}
    important_words = [w for w in words if len(w) > 2 and w.lower() not in stop_words]
    
    # Se não há palavras importantes, usa as primeiras palavras
    if not important_words:
        important_words = words[:5]
    
    # Constrói resumo com palavras importantes
    summary = ""
    for word in important_words:
        if len(summary + " " + word) <= max_length - 3:  # -3 para "..."
            summary += (" " if summary else "") + word
        else:
            break
    
    # Se conseguiu um resumo, adiciona "..."
    if summary:
        return summary + "..."
    
    # Fallback: pega as primeiras palavras até o limite
    summary = " ".join(words[:max_length // 5])  # Aproximadamente 5-6 palavras
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
    return summary


def get_session_summary(session_id: str, agent_id: str, db_id: Optional[str] = None, max_length: int = 30) -> str:
    """Extrai um resumo inteligente do assunto pesquisado da primeira mensagem da sessão"""
    # Cache simples para evitar múltiplas chamadas
    cache_key = f"summary_{session_id}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    try:
        history = get_session_history(session_id, agent_id, db_id)
        if not history:
            summary = "Sessão vazia"
            st.session_state[cache_key] = summary
            return summary
        
        # Procura a primeira mensagem do usuário
        for entry in history:
            if not entry:
                continue
            
            # Tenta extrair run_input (primeira mensagem do usuário)
            if "run_input" in entry and entry["run_input"] is not None:
                content = process_content(entry["run_input"])
                if content and content.strip():
                    # Cria resumo inteligente
                    summary = create_smart_summary(content, max_length)
                    st.session_state[cache_key] = summary
                    return summary
            
            # Tenta outros formatos
            if "message" in entry:
                msg = entry["message"]
                if isinstance(msg, dict):
                    content = process_content(msg.get("content", msg.get("text", "")))
                else:
                    content = process_content(msg)
                if content and content.strip():
                    summary = create_smart_summary(content, max_length)
                    st.session_state[cache_key] = summary
                    return summary
            
            if "input" in entry:
                content = process_content(entry["input"])
                if content and content.strip():
                    summary = create_smart_summary(content, max_length)
                    st.session_state[cache_key] = summary
                    return summary
        
        summary = "Sessão sem mensagens"
        st.session_state[cache_key] = summary
        return summary
    except:
        summary = "Sessão"
        st.session_state[cache_key] = summary
        return summary


def delete_session(session_id: str, db_id: Optional[str] = None, session_type: str = "agent") -> Tuple[bool, Optional[str]]:
    """Deleta uma sessão
    
    Args:
        session_id: ID da sessão a ser deletada
        db_id: ID do banco de dados (opcional)
        session_type: Tipo da sessão (padrão: "agent")
    
    Returns:
        tuple[bool, Optional[str]]: (sucesso, mensagem_erro)
    """
    if not session_id:
        return False, "Session ID não fornecido"
    
    try:
        # Monta parâmetros da query string
        params = {
            "type": session_type,
        }
        if db_id:
            params["db_id"] = db_id
        
        # Faz a requisição DELETE
        url = f"{API_BASE_URL}/sessions/{session_id}"
        response = requests.delete(
            url,
            params=params,
            timeout=10
        )
        
        # Status 200 (OK) e 204 (No Content) são considerados sucesso
        if response.status_code in [200, 204]:
            return True, None
        
        # Tenta extrair mensagem de erro da resposta
        error_msg = f"Erro HTTP {response.status_code}"
        try:
            # Tenta parsear como JSON
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                if isinstance(error_data, dict):
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                    elif "message" in error_data:
                        error_msg = error_data["message"]
                    elif "error" in error_data:
                        error_msg = error_data["error"]
            else:
                # Se não for JSON, pega o texto da resposta
                response_text = response.text.strip()
                if response_text:
                    error_msg = f"{error_msg}: {response_text[:200]}"
        except (json.JSONDecodeError, ValueError):
            # Se falhar ao parsear JSON, usa o texto da resposta
            response_text = response.text.strip()
            if response_text:
                error_msg = f"{error_msg}: {response_text[:200]}"
        
        return False, error_msg
            
    except requests.exceptions.ConnectionError as e:
        return False, f"Erro de conexão com a API ({API_BASE_URL}). Verifique se a API está rodando: {str(e)}"
    except requests.exceptions.Timeout:
        return False, "Timeout ao deletar sessão. A requisição demorou muito (>10s)."
    except requests.exceptions.RequestException as e:
        return False, f"Erro na requisição: {str(e)}"
    except Exception as e:
        return False, f"Erro inesperado ao deletar sessão: {str(e)}"


def parse_streaming_response(response):
    """Processa resposta streaming da API"""
    buffer = ""
    
    try:
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                buffer += chunk
                # Procura por objetos JSON completos no buffer
                while "{" in buffer:
                    start = buffer.find("{")
                    if start == -1:
                        break
                    
                    brace_count = 0
                    in_string = False
                    escape_next = False
                    end = -1
                    
                    for i in range(start, len(buffer)):
                        char = buffer[i]
                        
                        if in_string:
                            if escape_next:
                                escape_next = False
                            elif char == "\\":
                                escape_next = True
                            elif char == '"':
                                in_string = False
                        else:
                            if char == '"':
                                in_string = True
                            elif char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i
                                    break
                    
                    if end != -1:
                        json_str = buffer[start:end + 1]
                        buffer = buffer[end + 1:].lstrip()
                        try:
                            # Garante que o JSON seja parseado com encoding UTF-8
                            parsed = json.loads(json_str, strict=False)
                            yield parsed
                        except json.JSONDecodeError:
                            # Se falhar ao parsear, tenta encontrar o próximo {
                            next_start = buffer.find("{", start + 1)
                            if next_start == -1:
                                break
                            buffer = buffer[next_start:]
                            continue
                    else:
                        # JSON incompleto, espera mais dados
                        break
    except Exception as e:
        # Se houver erro no parsing, tenta processar o buffer restante
        if buffer.strip():
            try:
                # Tenta parsear como um único JSON
                yield json.loads(buffer)
            except:
                pass
        raise e


def send_message_stream(agent_id: str, message: str, session_id: Optional[str] = None, message_placeholder=None):
    """Envia mensagem para o agente e processa resposta streaming com atualização em tempo real
    
    Returns:
        tuple: (full_content, tool_calls) onde tool_calls é uma lista de dicionários com informações das ferramentas
    """
    try:
        url = f"{API_BASE_URL}/agents/{agent_id}/runs"
        
        form_data = {
            "message": message,
            "stream": "true",
        }
        if session_id:
            form_data["session_id"] = session_id
        
        response = requests.post(url, data=form_data, stream=True, timeout=300)
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = error_data.get("detail", f"Erro {response.status_code}: {response.text}")
            raise Exception(error_msg)
        
        full_content = ""
        current_session_id = session_id
        last_content = ""  # Armazena o último conteúdo recebido para detectar se é incremental
        tool_calls = []  # Lista para armazenar tool calls
        tool_calls_dict = {}  # Dicionário para rastrear tool calls por ID e evitar duplicatas
        
        for chunk in parse_streaming_response(response):
            event = chunk.get("event", "")
            
            # Captura session_id quando a sessão inicia
            if event in ["RunStarted", "ReasoningStarted"]:
                if chunk.get("session_id"):
                    current_session_id = chunk["session_id"]
                    if "current_session_id" not in st.session_state or st.session_state.current_session_id != current_session_id:
                        st.session_state.current_session_id = current_session_id
            
            # Captura tool calls (pode vir em qualquer chunk)
            if "tool" in chunk or "tools" in chunk:
                # Função auxiliar para processar tool_args garantindo UTF-8
                def process_tool_args(args):
                    """Processa tool_args garantindo encoding UTF-8"""
                    if not args:
                        return {}
                    if isinstance(args, dict):
                        processed = {}
                        for k, v in args.items():
                            # Garante que chaves e valores sejam strings UTF-8
                            key = k.decode('utf-8', errors='replace') if isinstance(k, bytes) else str(k)
                            if isinstance(v, bytes):
                                value = v.decode('utf-8', errors='replace')
                            elif isinstance(v, dict):
                                value = process_tool_args(v)  # Recursivo
                            elif isinstance(v, list):
                                value = [item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item for item in v]
                            else:
                                value = v
                            processed[key] = value
                        return processed
                    return args
                
                # Processa tool único
                if "tool" in chunk:
                    tool = chunk["tool"]
                    tool_id = tool.get("tool_call_id") or f"{tool.get('tool_name', 'unknown')}-{tool.get('created_at', time.time())}"
                    tool_args = process_tool_args(tool.get("tool_args", {}))
                    if tool_id not in tool_calls_dict:
                        tool_calls_dict[tool_id] = {
                            "tool_call_id": tool_id,
                            "tool_name": tool.get("tool_name", "unknown"),
                            "tool_args": tool_args,
                            "content": tool.get("content"),
                            "tool_call_error": tool.get("tool_call_error", False),
                            "created_at": tool.get("created_at", time.time())
                        }
                    else:
                        # Atualiza tool call existente
                        tool_calls_dict[tool_id].update({
                            "tool_args": tool_args if tool_args else tool_calls_dict[tool_id].get("tool_args", {}),
                            "content": tool.get("content", tool_calls_dict[tool_id].get("content")),
                            "tool_call_error": tool.get("tool_call_error", tool_calls_dict[tool_id].get("tool_call_error", False))
                        })
                
                # Processa array de tools
                if "tools" in chunk and isinstance(chunk["tools"], list):
                    for tool in chunk["tools"]:
                        tool_id = tool.get("tool_call_id") or f"{tool.get('tool_name', 'unknown')}-{tool.get('created_at', time.time())}"
                        tool_args = process_tool_args(tool.get("tool_args", {}))
                        if tool_id not in tool_calls_dict:
                            tool_calls_dict[tool_id] = {
                                "tool_call_id": tool_id,
                                "tool_name": tool.get("tool_name", "unknown"),
                                "tool_args": tool_args,
                                "content": tool.get("content"),
                                "tool_call_error": tool.get("tool_call_error", False),
                                "created_at": tool.get("created_at", time.time())
                            }
                        else:
                            # Atualiza tool call existente
                            tool_calls_dict[tool_id].update({
                                "tool_args": tool_args if tool_args else tool_calls_dict[tool_id].get("tool_args", {}),
                                "content": tool.get("content", tool_calls_dict[tool_id].get("content")),
                                "tool_call_error": tool.get("tool_call_error", tool_calls_dict[tool_id].get("tool_call_error", False))
                            })
            
            # Captura conteúdo da resposta e atualiza em tempo real
            elif event in ["RunContent", "TeamRunContent"]:
                content = chunk.get("content", "")
                if isinstance(content, str):
                    # A API do AgentOS envia conteúdo completo acumulado em cada chunk
                    # Extrai apenas a parte nova removendo o conteúdo anterior
                    if last_content and content.startswith(last_content):
                        # Conteúdo completo: extrai apenas a parte nova
                        new_content = content[len(last_content):]
                        full_content += new_content
                    else:
                        # Primeiro chunk ou conteúdo não começa com o anterior (incremental puro)
                        # Se não começa com o anterior, assume que é incremental e faz append
                        if last_content:
                            full_content += content
                        else:
                            full_content = content
                    
                    # Atualiza a UI em tempo real com o conteúdo acumulado
                    if message_placeholder and full_content:
                        message_placeholder.markdown(full_content)
                    
                    # Atualiza o último conteúdo recebido (do chunk, não do full_content)
                    # Isso permite detectar se o próximo chunk é completo ou incremental
                    last_content = content
                elif content is not None:
                    # Conteúdo não é string, converte para JSON
                    full_content = json.dumps(content, ensure_ascii=False, indent=2)
                    if message_placeholder:
                        message_placeholder.markdown(f"```json\n{full_content}\n```")
                    last_content = full_content
            
            # Atualiza conteúdo final quando completa
            elif event in ["RunCompleted", "TeamRunCompleted"]:
                content = chunk.get("content", "")
                if isinstance(content, str):
                    full_content = content
                elif content is not None:
                    full_content = json.dumps(content, ensure_ascii=False, indent=2)
                
                # Garante que o conteúdo final seja exibido
                if message_placeholder:
                    message_placeholder.markdown(full_content)
            
            # Trata erros
            elif event in ["RunError", "TeamRunError"]:
                error_content = chunk.get("content", "Erro desconhecido")
                raise Exception(str(error_content))
        
        # Converte dicionário de tool calls para lista ordenada por created_at
        tool_calls = sorted(tool_calls_dict.values(), key=lambda x: x.get("created_at", 0))
        
        # Atualiza session_id no estado se foi criada nova sessão
        if current_session_id and current_session_id != session_id:
            st.session_state.current_session_id = current_session_id
            # Força atualização da lista de sessões
            if "sessions_updated" in st.session_state:
                st.session_state.sessions_updated = False
        
        return full_content, tool_calls
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro de conexão com a API: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro ao processar resposta: {str(e)}")


# ============================================
# FUNÇÕES DE UI PARA FERRAMENTAS
# ============================================

def format_tool_args(tool_args) -> str:
    """Formata tool_args garantindo encoding UTF-8 e acentuação correta"""
    if not tool_args:
        return ""
    
    try:
        if isinstance(tool_args, dict):
            # Garante que todos os valores sejam strings UTF-8 válidas
            formatted_args = {}
            for key, value in tool_args.items():
                # Processa a chave
                if isinstance(key, bytes):
                    key = key.decode('utf-8', errors='replace')
                elif not isinstance(key, str):
                    key = str(key)
                
                # Processa o valor
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='replace')
                elif isinstance(value, dict):
                    # Recursivamente processa dicionários aninhados
                    value = {k: (v.decode('utf-8', errors='replace') if isinstance(v, bytes) else v) 
                            for k, v in value.items()}
                elif isinstance(value, list):
                    # Processa listas
                    value = [item.decode('utf-8', errors='replace') if isinstance(item, bytes) else item 
                            for item in value]
                elif not isinstance(value, (str, int, float, bool, type(None))):
                    value = str(value)
                
                formatted_args[key] = value
            
            # Converte para JSON com encoding UTF-8
            return json.dumps(formatted_args, ensure_ascii=False, indent=2)
        elif isinstance(tool_args, str):
            # Se já é string, garante encoding UTF-8
            if isinstance(tool_args, bytes):
                return tool_args.decode('utf-8', errors='replace')
            return tool_args
        else:
            # Converte para string garantindo UTF-8
            result = str(tool_args)
            if isinstance(result, bytes):
                return result.decode('utf-8', errors='replace')
            return result
    except Exception as e:
        # Em caso de erro, tenta converter de forma segura
        try:
            return json.dumps(tool_args, ensure_ascii=False, indent=2, default=str)
        except:
            return str(tool_args)


def display_tool_calls(tool_calls: List[Dict], message_key: str):
    """Exibe as ferramentas usadas pelo agente com detalhes clicáveis"""
    if not tool_calls:
        return
    
    st.markdown("**🔧 Ferramentas utilizadas:**")
    
    for idx, tool_call in enumerate(tool_calls):
        tool_name = tool_call.get("tool_name", "Ferramenta desconhecida")
        tool_args = tool_call.get("tool_args", {})
        tool_error = tool_call.get("tool_call_error", False)
        tool_content = tool_call.get("content")
        
        # Cria uma chave única para cada tool call
        tool_key = f"{message_key}_tool_{idx}"
        
        # Exibe badge da ferramenta
        error_indicator = " ❌" if tool_error else ""
        with st.expander(f"🔧 {tool_name}{error_indicator}", expanded=False):
            # Mostra argumentos/query executada
            if tool_args:
                st.markdown("**📝 Query/Argumentos executados:**")
                # Formata tool_args garantindo encoding UTF-8
                args_str = format_tool_args(tool_args)
                st.code(args_str, language="json")
            
            # Mostra resultado da execução (se disponível)
            if tool_content:
                st.markdown("**📤 Resultado da execução:**")
                if isinstance(tool_content, str):
                    # Se for muito longo, mostra em um expander
                    if len(tool_content) > 500:
                        st.text_area("", tool_content, height=200, key=f"{tool_key}_content", disabled=True, label_visibility="collapsed")
                    else:
                        st.code(tool_content, language="text")
                elif isinstance(tool_content, dict):
                    st.json(tool_content)
                else:
                    st.write(tool_content)
            
            # Mostra erro se houver
            if tool_error:
                st.error("⚠️ Esta ferramenta retornou um erro durante a execução.")
            
            # Mostra informações adicionais
            created_at = tool_call.get("created_at", 0)
            if created_at:
                try:
                    dt = datetime.fromtimestamp(created_at)
                    st.caption(f"Executado em: {dt.strftime('%d/%m/%Y %H:%M:%S')}")
                except:
                    pass


# ============================================
# INICIALIZAÇÃO DO ESTADO
# ============================================

def init_session_state():
    """Inicializa estado da sessão Streamlit"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    
    if "selected_agent_id" not in st.session_state:
        st.session_state.selected_agent_id = None
    
    if "sessions_updated" not in st.session_state:
        st.session_state.sessions_updated = False
    
    if "agent_db_id" not in st.session_state:
        st.session_state.agent_db_id = None


# ============================================
# INTERFACE DO USUÁRIO
# ============================================

def main():
    st.set_page_config(
        page_title="Copywriter Modelador - Chat",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    # Título principal
    st.title("💬 Chat com Agente de Copywriting")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Seleção de Agente
        st.subheader("🤖 Agente")
        agents = get_agents()
        
        # Mapeia agentes para formato esperado
        agent_options = {}
        for agent in agents:
            # Tenta diferentes campos para ID e nome
            agent_id = agent.get('id') or agent.get('agent_id') or agent.get('_id')
            agent_name = agent.get('name') or agent.get('agent_name') or agent_id or 'Unknown'
            if agent_id:
                agent_options[f"{agent_name}"] = agent_id
        
        agent_names = list(agent_options.keys())
        
        if not agent_names:
            st.warning("⚠️ Nenhum agente disponível. Verifique se a API está rodando em " + API_BASE_URL)
            st.info("💡 Inicie a API com: `uv run uvicorn agent:app --host 0.0.0.0 --port 8000`")
        else:
            selected_agent_name = st.selectbox(
                "Selecione o agente:",
                options=agent_names,
                index=0,
                key="agent_selector"
            )
            
            if selected_agent_name:
                st.session_state.selected_agent_id = agent_options[selected_agent_name]
                # Busca db_id do agente se disponível
                selected_agent = next((a for a in agents if (a.get('id') or a.get('agent_id') or a.get('_id')) == st.session_state.selected_agent_id), None)
                if selected_agent:
                    st.session_state.agent_db_id = selected_agent.get('db_id')
        
        st.divider()
        
        # Gerenciamento de Sessões
        st.subheader("💾 Sessões")
        
        if st.session_state.selected_agent_id:
            # Botão para criar nova sessão
            if st.button("➕ Nova Sessão", use_container_width=True):
                st.session_state.current_session_id = None
                st.session_state.messages = []
                st.session_state.sessions_updated = False
                st.rerun()
            
            st.divider()
            
            # Lista de sessões
            sessions = get_sessions(st.session_state.selected_agent_id, st.session_state.agent_db_id)
            
            if sessions:
                st.write("**Sessões disponíveis:**")
                
                # CSS customizado para tornar os botões menores e mais discretos (aplica apenas uma vez)
                st.markdown(
                    """
                    <style>
                    /* Botões de sessão */
                    div[data-testid="stButton"] > button[kind="secondary"] {
                        height: 3rem;
                        padding-top: 0.5rem;
                        padding-bottom: 0.5rem;
                        padding-left: 0.75rem;
                        padding-right: 0.75rem;
                        font-size: 0.6rem;
                        line-height: 1.2;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        max-width: 100%;
                    }
                    /* Botão de deletar - garante que o ícone fique dentro e centralizado */
                    div[data-testid="column"]:nth-child(2) button {
                        min-width: 2.5rem !important;
                        width: 100% !important;
                        height: 3rem !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                        padding: 0.5rem !important;
                        font-size: 1.2rem !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                
                # Ordena sessões por data de criação (mais recentes primeiro)
                sessions_sorted = sorted(sessions, key=lambda x: x.get('created_at', 0), reverse=True)
                
                for session in sessions_sorted:
                    session_id = session.get('session_id', '')
                    
                    # Extrai resumo inteligente do assunto da primeira mensagem
                    summary = get_session_summary(
                        session_id,
                        st.session_state.selected_agent_id,
                        st.session_state.agent_db_id,
                        max_length=30
                    )
                    
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        # Botão para selecionar sessão - discreto e pequeno
                        if st.button(
                            summary,
                            key=f"session_{session_id}",
                            use_container_width=True,
                            type="secondary"  # Torna o botão mais discreto
                        ):
                            st.session_state.current_session_id = session_id
                            st.session_state.messages = []
                            
                            # Carrega histórico da sessão
                            try:
                                with st.spinner("Carregando histórico da sessão..."):
                                    history = get_session_history(
                                        session_id,
                                        st.session_state.selected_agent_id,
                                        st.session_state.agent_db_id
                                    )
                                
                                if not history:
                                    st.info("Esta sessão não possui histórico de conversas.")
                                else:
                                    # Converte histórico para formato de mensagens
                                    # A API pode retornar runs com diferentes estruturas:
                                    # 1. { "run_input": "...", "run_output": {...} }
                                    # 2. { "message": {...}, "response": {...} }
                                    # 3. { "input": "...", "output": "..." }
                                    
                                    # Debug: mostra quantos runs foram encontrados
                                    if len(history) > 0:
                                        st.caption(f"📊 Carregando {len(history)} interação(ões) do histórico...")
                                    
                                    # Debug: mostra estrutura do primeiro entry para diagnóstico
                                    debug_info = []
                                    
                                    for idx, entry in enumerate(history):
                                        if not entry:
                                            continue
                                        
                                        # Debug: captura estrutura do primeiro entry
                                        if idx == 0:
                                            debug_info.append(f"**Estrutura do primeiro entry:**")
                                            debug_info.append(f"- Chaves disponíveis: {list(entry.keys())}")
                                            if "run_input" in entry:
                                                debug_info.append(f"- run_input tipo: {type(entry['run_input']).__name__}")
                                            if "run_output" in entry:
                                                debug_info.append(f"- run_output tipo: {type(entry['run_output']).__name__}")
                                            if "response" in entry:
                                                debug_info.append(f"- response tipo: {type(entry['response']).__name__}")
                                            if "content" in entry:
                                                debug_info.append(f"- content tipo: {type(entry['content']).__name__}")
                                        
                                        # Processa mensagem do usuário (run_input)
                                        user_content = None
                                        user_created_at = 0
                                        
                                        # Prioriza run_input (formato padrão da API)
                                        if "run_input" in entry and entry["run_input"] is not None:
                                            user_content = process_content(entry["run_input"])
                                            user_created_at = entry.get("created_at", 0)
                                        # Tenta outros formatos
                                        elif "message" in entry:
                                            msg = entry["message"]
                                            if isinstance(msg, dict):
                                                user_content = process_content(msg.get("content", msg.get("text", "")))
                                                user_created_at = msg.get("created_at", entry.get("created_at", 0))
                                            else:
                                                user_content = process_content(msg)
                                                user_created_at = entry.get("created_at", 0)
                                        elif "input" in entry:
                                            user_content = process_content(entry["input"])
                                            user_created_at = entry.get("created_at", 0)
                                        
                                        # Adiciona mensagem do usuário se encontrada
                                        if user_content and user_content.strip():
                                            st.session_state.messages.append({
                                                "role": "user",
                                                "content": user_content,
                                                "created_at": user_created_at
                                            })
                                        
                                        # Processa resposta do assistente (run_output)
                                        assistant_content = None
                                        assistant_created_at = 0
                                        tool_calls = []
                                        
                                        # Prioriza run_output (formato padrão da API)
                                        if "run_output" in entry:
                                            output = entry["run_output"]
                                            # run_output pode ser string, dict, objeto complexo ou None/vazio
                                            if output is not None:
                                                processed = process_content(output)
                                                # Só usa se o conteúdo processado não estiver vazio
                                                if processed and processed.strip():
                                                    assistant_content = processed
                                                    assistant_created_at = entry.get("created_at", 0)
                                        
                                        # Tenta response (formato ChatEntry)
                                        if not assistant_content and "response" in entry:
                                            resp = entry["response"]
                                            if isinstance(resp, dict):
                                                assistant_content = process_content(resp.get("content", resp.get("text", "")))
                                                assistant_created_at = resp.get("created_at", entry.get("created_at", 0))
                                                # Extrai tool_calls se disponível
                                                if "tool_calls" in resp:
                                                    tool_calls = resp["tool_calls"] if isinstance(resp["tool_calls"], list) else []
                                                elif "tools" in resp:
                                                    tool_calls = resp["tools"] if isinstance(resp["tools"], list) else []
                                            else:
                                                assistant_content = process_content(resp)
                                                assistant_created_at = entry.get("created_at", 0)
                                        
                                        # Tenta output
                                        if not assistant_content and "output" in entry:
                                            assistant_content = process_content(entry["output"])
                                            assistant_created_at = entry.get("created_at", 0)
                                        
                                        # Tenta content no nível raiz (pode ser resposta se não for user_content)
                                        # IMPORTANTE: Verifica se content é diferente de user_content para evitar duplicatas
                                        if not assistant_content and "content" in entry:
                                            content_value = entry["content"]
                                            processed_content = process_content(content_value)
                                            # Só usa como resposta se for diferente da mensagem do usuário
                                            if processed_content and processed_content != user_content:
                                                assistant_content = processed_content
                                                assistant_created_at = entry.get("created_at", 0)
                                        
                                        # Extrai tool_calls do entry se disponível (em qualquer nível)
                                        if not tool_calls:
                                            if "tool_calls" in entry:
                                                tool_calls = entry["tool_calls"] if isinstance(entry["tool_calls"], list) else []
                                            elif "tools" in entry:
                                                tool_calls = entry["tools"] if isinstance(entry["tools"], list) else []
                                            elif "tool" in entry:
                                                tool_calls = [entry["tool"]] if isinstance(entry["tool"], dict) else []
                                        
                                        # Extrai tool_calls de response se ainda não encontrou
                                        if not tool_calls and "response" in entry:
                                            resp = entry["response"]
                                            if isinstance(resp, dict):
                                                if "tool_calls" in resp:
                                                    tool_calls = resp["tool_calls"] if isinstance(resp["tool_calls"], list) else []
                                                elif "tools" in resp:
                                                    tool_calls = resp["tools"] if isinstance(resp["tools"], list) else []
                                        
                                        # Adiciona resposta do assistente se encontrada
                                        # IMPORTANTE: Adiciona mesmo que seja vazio se houver tool_calls, para manter contexto
                                        if assistant_content and assistant_content.strip():
                                            assistant_msg = {
                                                "role": "assistant",
                                                "content": assistant_content,
                                                "created_at": assistant_created_at if assistant_created_at else entry.get("created_at", 0)
                                            }
                                            if tool_calls:
                                                assistant_msg["tool_calls"] = tool_calls
                                            st.session_state.messages.append(assistant_msg)
                                        elif tool_calls:
                                            # Se não há conteúdo mas há tool_calls, adiciona mensagem vazia com tool_calls
                                            assistant_msg = {
                                                "role": "assistant",
                                                "content": "",
                                                "created_at": assistant_created_at if assistant_created_at else entry.get("created_at", 0)
                                            }
                                            assistant_msg["tool_calls"] = tool_calls
                                            st.session_state.messages.append(assistant_msg)
                                    
                                    # Ordena mensagens por timestamp para garantir ordem correta
                                    st.session_state.messages.sort(key=lambda x: x.get("created_at", 0))
                                    
                                    # Resumo do que foi carregado
                                    user_msgs = [m for m in st.session_state.messages if m.get("role") == "user"]
                                    assistant_msgs = [m for m in st.session_state.messages if m.get("role") == "assistant"]
                                    
                                    # Mostra informações de debug se houver
                                    if debug_info:
                                        with st.expander("🔍 Informações de debug (primeiro entry)"):
                                            for info in debug_info:
                                                st.markdown(info)
                                    
                                    if user_msgs or assistant_msgs:
                                        st.success(f"✅ Histórico carregado: {len(user_msgs)} pergunta(s) e {len(assistant_msgs)} resposta(s)")
                                    else:
                                        st.warning("⚠️ Nenhuma mensagem foi carregada. Verifique a estrutura dos dados retornados pela API.")
                                
                            except Exception as e:
                                st.error(f"Erro ao carregar histórico da sessão: {str(e)}")
                                # Adiciona informações de debug em caso de erro
                                with st.expander("🔍 Detalhes do erro"):
                                    st.write(f"**Exception:** `{type(e).__name__}`")
                                    st.write(f"**Mensagem:** `{str(e)}`")
                                    if history:
                                        st.write(f"**Runs encontrados:** {len(history)}")
                                        st.write("**Primeiro run (amostra):**")
                                        st.json(history[0] if history else {})
                            
                            st.rerun()
                    
                    with col2:
                        # Botão para deletar sessão - ajustado para manter o ícone dentro
                        if st.button("🗑", key=f"delete_{session_id}", help="Deletar sessão", use_container_width=True):
                            try:
                                success, error_msg = delete_session(session_id, st.session_state.agent_db_id)
                                if success:
                                    st.success("✅ Sessão deletada com sucesso!")
                                    if st.session_state.current_session_id == session_id:
                                        st.session_state.current_session_id = None
                                        st.session_state.messages = []
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    # Exibe erro detalhado
                                    error_display = error_msg or "Erro desconhecido ao deletar sessão"
                                    st.error(f"❌ Erro ao deletar sessão:\n{error_display}")
                                    # Adiciona informações de debug (apenas em caso de erro)
                                    with st.expander("🔍 Detalhes do erro"):
                                        st.write(f"**Session ID:** `{session_id}`")
                                        st.write(f"**DB ID:** `{st.session_state.agent_db_id or 'Não fornecido'}`")
                                        st.write(f"**API URL:** `{API_BASE_URL}`")
                            except Exception as e:
                                st.error(f"❌ Erro inesperado ao deletar sessão: {str(e)}")
                                with st.expander("🔍 Detalhes do erro"):
                                    st.write(f"**Exception:** `{type(e).__name__}`")
                                    st.write(f"**Mensagem:** `{str(e)}`")
            else:
                st.info("Nenhuma sessão encontrada. Crie uma nova sessão enviando uma mensagem.")
        else:
            st.info("Selecione um agente primeiro.")
        
        st.divider()
        
        # Informações da API
        st.subheader("🔌 API")
        st.write(f"**URL:** {API_BASE_URL}")
        if st.button("🔄 Verificar Conexão"):
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ API conectada!")
                else:
                    st.error(f"❌ API retornou status {response.status_code}")
            except Exception as e:
                st.error(f"❌ Erro de conexão: {str(e)}")
    
    # Área principal do chat
    if not st.session_state.selected_agent_id:
        st.info("👈 Selecione um agente na barra lateral para começar.")
        return
    
    # Exibe histórico de mensagens
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Exibe ferramentas se houver
            if message.get("tool_calls"):
                display_tool_calls(message["tool_calls"], f"msg_{idx}")
    
    # Input de mensagem
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adiciona mensagem do usuário
        user_message = {
            "role": "user",
            "content": prompt,
            "created_at": time.time()
        }
        st.session_state.messages.append(user_message)
        
        # Exibe mensagem do usuário
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Exibe mensagem do assistente (streaming)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            status_placeholder = st.empty()
            full_response = ""
            
            try:
                # Mostra indicador de processamento
                status_placeholder.info("⏳ Processando...")
                
                # Envia mensagem e processa streaming com atualização em tempo real
                full_response, tool_calls = send_message_stream(
                    st.session_state.selected_agent_id,
                    prompt,
                    st.session_state.current_session_id,
                    message_placeholder
                )
                
                # Remove indicador de processamento
                status_placeholder.empty()
                
                # Garante que a resposta final seja exibida
                if full_response:
                    message_placeholder.markdown(full_response)
                else:
                    message_placeholder.info("Resposta vazia do agente.")
                
                # Exibe ferramentas utilizadas
                if tool_calls:
                    display_tool_calls(tool_calls, f"current_msg_{len(st.session_state.messages)}")
                
                # Adiciona resposta do assistente ao histórico
                assistant_message = {
                    "role": "assistant",
                    "content": full_response,
                    "created_at": time.time()
                }
                if tool_calls:
                    assistant_message["tool_calls"] = tool_calls
                st.session_state.messages.append(assistant_message)
                
                # Atualiza lista de sessões se nova sessão foi criada
                if st.session_state.current_session_id:
                    st.session_state.sessions_updated = False
            
            except Exception as e:
                status_placeholder.empty()
                error_message = f"❌ Erro: {str(e)}"
                message_placeholder.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "created_at": time.time()
                })


if __name__ == "__main__":
    main()

