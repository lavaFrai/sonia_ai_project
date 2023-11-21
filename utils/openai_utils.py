import datetime
import json
import time
from pathlib import Path

import openai
import aiohttp
from moviepy.video.io.VideoFileClip import VideoFileClip

from main import server


async def chatgpt_generate_one_message(system_prompt: str, user_prompt: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]


async def chatgpt_continue_dialog(history: list) -> dict:
    history[0]['content'] = history[0]['content'].replace('%time%', datetime.datetime.now().strftime('%Y %B %d %H:%M:%S'))
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo-1106",
        messages=history
    )
    return response["choices"][0]["message"]


async def whisper_transcribe_voice(file: open):
    response = await openai.Audio.atranscribe(
        model='whisper-1',
        file=file
    )
    return response['text']


async def whisper_transcribe_voice_in_video(file: str):
    video = VideoFileClip(file)
    audio_file = await server.create_file(ex='mp3')
    audio = video.audio
    audio.write_audiofile(audio_file)

    audio.close()
    video.close()

    response = await openai.Audio.atranscribe(
        model='whisper-1',
        file=open(file, 'rb')
    )
    await server.delete_file(audio_file)
    return response['text']


async def openai_text_to_speech(text: str, file: str, voice="shimmer"):
    from openai import api_requestor

    headers = {
        "Authorization": "Bearer " + server.config.openai_token,
        "Content-Type": "application/json"
    }
    data = {
        "model": "tts-1-hd",
        "voice": voice,
        "input": text
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/audio/speech', headers=headers, data=json.dumps(data)) as response:
            with open(file, "wb") as f:
                while True:
                    chunk = await response.content.readany()
                    if not chunk:
                        break
                    f.write(chunk)
