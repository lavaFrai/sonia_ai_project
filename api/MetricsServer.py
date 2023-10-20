import json
import time

from aiohttp import web


class MetricsServer:
    def __init__(self):
        self.start_time = time.time()
        self.errors = 0
        self.unhandled_errors = 0
        self.messages = 0
        self.callbacks = 0

        self.chat_messages = 0
        self.chat_voice_messages = 0
        self.chat_video_messages = 0

        self.images_generated = 0
        self.images_extended = 0

        self.voices_transcribed = 0
        self.videos_transcribed = 0

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
            "messages": self.messages,
            "callbacks": self.callbacks,

            "chat_messages": self.chat_messages,
            "chat_voice_messages": self.chat_voice_messages,
            "chat_video_messages": self.chat_video_messages,
            "images_generated": self.images_generated,
            "images_extended": self.images_extended,
            "voices_transcribed": self.voices_transcribed,
            "videos_transcribed": self.videos_transcribed,
        }
        return self.json_response(metrics)

    def add_error(self):
        self.errors += 1

    def add_unhandled_error(self):
        self.unhandled_errors += 1

    def add_message(self):
        self.messages += 1

    def add_callback(self):
        self.callbacks += 1
