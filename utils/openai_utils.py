import openai
from moviepy.video.io.VideoFileClip import VideoFileClip

from main import server


async def chatgpt_generate_one_message(system_prompt: str, user_prompt: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo-16k",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]


async def chatgpt_continue_dialog(history: dict) -> dict:
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo-16k",
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
