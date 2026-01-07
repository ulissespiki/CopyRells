from transcription_reader import get_creator_transcriptions, list_available_creators

influenciador = input("Digite o nome do influenciador: ")

print(get_creator_transcriptions(influenciador))