import json
import os
import aiohttp

api_key = os.environ.get("GEMINI_API_KEY")
base_url = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")


class ApiClient:
    def __init__(self):
        self.api_key = api_key
        self.base_url = base_url

    async def request(self, path, body=""):
        url = self.base_url + path + "?key=" + self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(body)) as response:
                resp = await response.text()
                return await response.json()
