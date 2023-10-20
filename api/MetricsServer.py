import json
import time

from aiohttp import web


class MetricsServer:
    def __init__(self):
        self.start_time = time.time()
        self.errors = 0
        self.unhandled_errors = 0

        self.app = web.Application()
        self.app.add_routes([web.get('/hello', self.on_hello)])
        self.app.add_routes([web.get('/metrics', self.on_metrics)])

    async def run(self):
        runner = web.AppRunner(self.app)
        await runner.setup()

        await web.TCPSite(
            runner,
            '0.0.0.0',
            port=80
        ).start()

    @staticmethod
    def json_response(json_object, code=200):
        return web.Response(text=json.dumps(json_object), status=code)

    async def on_hello(self, request):
        return self.json_response({
            "message": "Hello! Sonia bot is working!"
        })

    async def on_metrics(self, request):
        metrics = {
            "uptime": time.time() - self.start_time,
            "handled_errors": self.errors,
            "unhandled_errors": self.unhandled_errors,
        }
        return self.json_response(metrics)

    def add_error(self):
        self.errors += 1

    def add_unhandled_error(self):
        self.unhandled_errors += 1
