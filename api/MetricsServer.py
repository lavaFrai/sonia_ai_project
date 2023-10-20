import json

from aiohttp import web


class MetricsServer:
    def __init__(self):
        self.app = web.Application()
        self.app.add_routes([web.get('/hello', self.on_hello)])

    async def run(self):
        runner = web.AppRunner(self.app)
        await runner.setup()

        await web.TCPSite(
            runner,
            '0.0.0.0',
            port=80
        ).start()

    @staticmethod
    async def json_response(json_object, code=200):
        return web.Response(text=json.dumps(json_object), status=code)

    async def on_hello(self, request):
        return await self.json_response({
            "message": "Hello! Sonia bot is working!"
        })
