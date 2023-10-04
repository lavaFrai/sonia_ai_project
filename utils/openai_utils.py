import openai


async def chatgpt_generate_one_message(system_prompt: str, user_prompt: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]


async def chatgpt_continue_dialog(history: dict) -> dict:
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=history
    )
    return response["choices"][0]["message"]
