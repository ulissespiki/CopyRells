import json
from pathlib import Path


def get_creator_transcriptions(creator_name):
    """
    Lê as transcrições de um criador específico do arquivo JSON
    e retorna formatado em markdown.
    
    Args:
        creator_name (str): Nome do criador (ex: 'jeffnippard', 'kallaway')
    
    Returns:
        str: Transcrições formatadas em markdown ou mensagem de erro
    """
    try:
        with open('transcriptions.json', 'r', encoding='utf-8') as f:
            transcriptions = json.load(f)
        
        if creator_name not in transcriptions:
            return f"Criador '{creator_name}' não encontrado. Criadores disponíveis: {list(transcriptions.keys())}"
        
        creator_transcriptions = transcriptions[creator_name]
        
        if not creator_transcriptions:
            return f"Nenhuma transcrição encontrada para o criador '{creator_name}'"
        
        formatted_transcriptions = []
        for i, item in enumerate(creator_transcriptions, 1):
            video_name = item['video']
            transcription = item['transcription']
            formatted_transcriptions.append(f"Transcript {i}\n{transcription}")
        
        return "\n\n".join(formatted_transcriptions)
        
    except FileNotFoundError:
        return "Arquivo transcriptions.json não encontrado. Execute transcripter.py primeiro."
    except json.JSONDecodeError:
        return "Erro ao ler o arquivo transcriptions.json. Arquivo corrompido."
    except Exception as e:
        return f"Erro inesperado: {str(e)}"



def list_available_creators():
    """
    Lista todos os criadores disponíveis no arquivo JSON.
    
    Returns:
        str: Lista de criadores disponíveis
    """
    try:
        with open('transcriptions.json', 'r', encoding='utf-8') as f:
            transcriptions = json.load(f)
        
        creators = list(transcriptions.keys())
        if creators:
            return f"Criadores disponíveis: {', '.join(creators)}"
        else:
            return "Nenhum criador encontrado no arquivo."
            
    except FileNotFoundError:
        return "Arquivo transcriptions.json não encontrado."
    except Exception as e:
        return f"Erro ao listar criadores: {str(e)}"

