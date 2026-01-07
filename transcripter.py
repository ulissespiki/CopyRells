import os
import json
import subprocess
import tempfile
from pathlib import Path
from groq import Groq
import base64
from dotenv import load_dotenv

load_dotenv()

def extract_audio(video_path, audio_path):
    cmd = [
        'ffmpeg', '-i', video_path, 
        '-vn', '-acodec', 'mp3', 
        '-ar', '16000', '-ac', '1', audio_path, '-y'
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def transcribe_audio(audio_path, client):
    with open(audio_path, 'rb') as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            response_format="text"
        )
    
    return response

def process_videos():
    videos_dir = Path('videos')
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    transcriptions = {}
    
    for creator_dir in videos_dir.iterdir():
        if creator_dir.is_dir():
            creator_name = creator_dir.name
            transcriptions[creator_name] = []
            
            for video_file in creator_dir.glob('*.mp4'):
                print(f'Processando: {video_file}')
                
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
                    audio_path = temp_audio.name
                
                try:
                    extract_audio(str(video_file), audio_path)
                    transcription = transcribe_audio(audio_path, client)
                    
                    transcriptions[creator_name].append({
                        'video': video_file.name,
                        'transcription': transcription
                    })
                    
                except Exception as e:
                    print(f'Erro ao processar {video_file}: {e}')
                finally:
                    os.unlink(audio_path)
    
    with open('transcriptions.json', 'w', encoding='utf-8') as f:
        json.dump(transcriptions, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    process_videos()
