from .chat_client import ChatClient


async def gemini_transcribe_voice(file):
    chat = ChatClient(system_instruction="You must transcribe the voice message. Write without mistakes. Correct mistakes and keep track of punctuation.")
    return await chat.send_media_message(file.read(), "audio/mp3")
