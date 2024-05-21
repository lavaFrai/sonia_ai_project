import base64
import json

from .client import ApiClient


class ChatClient:
    def __init__(self, history=None, system_instruction=""):
        if history is None:
            self.history = []
        else:
            self.history = history

        self.system_instruction = system_instruction

        self.model = "gemini-1.5-pro-latest"
        self.api = ApiClient()

    async def send_message(self, message: str) -> str:
        self.history.append(self.build_text_message(message, "user"))

        response = await self.api.request(f"/v1beta/models/{self.model}:generateContent",
                                          self.build_request_body_by_history())
        response_message = response["candidates"][0]["content"]["parts"][0]["text"]
        self.history.append(self.build_text_message(response_message, "model"))

        return response_message

    async def send_media_message(self, file: bytes, mime_type: str) -> str:
        self.history.append(self.build_file_message(file, mime_type, "user"))

        response = await self.api.request(f"/v1beta/models/{self.model}:generateContent",
                                          self.build_request_body_by_history())
        try:
            response_message = response["candidates"][0]["content"]["parts"][0]["text"]
        except KeyError:
            print(json.dumps(response, indent=4))
            raise RuntimeError("Response message error")
        self.history.append(self.build_text_message(response_message, "model"))

        return response_message

    async def send_multiple_messages(self, messages: list) -> str:
        self.history.extend(messages)

        response = await self.api.request(f"/v1beta/models/{self.model}:generateContent",
                                          self.build_request_body_by_history())
        try:
            response_message = response["candidates"][0]["content"]["parts"][0]["text"]
        except KeyError:
            print(json.dumps(response, indent=4))
            raise RuntimeError("Response message error")
        self.history.append(self.build_text_message(response_message, "model"))

        return response_message


    def build_request_body_by_history(self):
        return {
            "contents": self.history,
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
            ],
            "systemInstruction": {
                "parts": {
                    "text": self.system_instruction
                }
            }
        }

    def get_history(self):
        return self.history

    @staticmethod
    def build_text_message(message: str, role: str):
        return {
            "role": role,
            "parts": {
                "text": message
            }
        }

    @staticmethod
    def build_file_message(file: bytes, mime_type: str, role: str):
        return {
            "role": role,
            "parts": {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": base64.b64encode(file).decode("utf-8")
                }
            }
        }
