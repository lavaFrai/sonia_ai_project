import openai


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
