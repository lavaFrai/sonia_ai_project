import asyncio
import json
import os
import aiohttp

api_key = []
global current_api_key
current_api_key = 0
base_url = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
proxy = None


class PayloadToLargeException(Exception):
    pass


class ApiClient:
    def __init__(self):
        self.api_key = api_key
        self.base_url = base_url
        self.proxy = proxy

    async def request(self, path, body="", attempts=5):
        url = self.base_url + path + "?key=" + await self.next_api_key()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(body), proxy=self.proxy) as response:
                resp = await response.text()
                if response.status == 413:
                    raise PayloadToLargeException()
                elif response.status == 429:
                    await asyncio.sleep(5)
                    return await self.request(path, body)
                elif response.status == 500:
                    print(resp)
                    if attempts == 0:
                        raise Exception(f"Failed to make request: {response.status}")
                    await asyncio.sleep(5)
                    return await self.request(path, body, attempts - 1)
                elif response.status != 200:
                    print(resp)
                    raise Exception(f"Failed to make request: {response.status}")
                return await response.json()

    async def push(self, path, body=""):
        url = self.base_url + path + "?key=" + await self.next_api_key()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=body) as response:
                resp = await response.text()
                if response.status == 413:
                    raise PayloadToLargeException()
                return await response.json()

    async def next_api_key(self):
        global current_api_key
        current_api_key += 1

        if current_api_key == len(api_key):
            current_api_key = 0

        return api_key[current_api_key]
