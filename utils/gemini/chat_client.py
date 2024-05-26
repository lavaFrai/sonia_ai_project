import base64
import json

from .client import ApiClient


class ChatClient:
    def __init__(self, history=None, system_instruction="", tools=None):
        if history is None:
            self.history = []
        else:
            self.history = history

        self.new_messages = []

        if tools is None:
            self.tools = []
        else:
            self.tools = tools

        self.system_instruction = system_instruction

        self.model = "gemini-1.5-pro-latest"
        self.api = ApiClient()

    async def send_message(self, message: str) -> str:
        response_message = await self.send_and_process_response([self.build_text_message(message, "user")])

        return response_message

    async def send_media_message(self, file: bytes, mime_type: str) -> str:
        response_message = await self.send_and_process_response([self.build_file_message(file, mime_type, "user")])

        return response_message

    async def send_multiple_messages(self, messages: list) -> str:
        response_message = await self.send_and_process_response(messages)

        return response_message

    def set_history(self, history):
        self.history = history

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
            },
            "tools": self.get_available_tools()
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

    @staticmethod
    def build_function_result_message(result: str):
        return {
            "role": "user",
            "parts": {
                "text": result
            }
        }

    def get_available_tools(self):
        return [
            {
                "functionDeclarations": {
                    "name": tool.get_name(),
                    "description": tool.get_description(),
                    "parameters": tool.get_parameters(),
                }
            } for tool in self.tools
        ]

    async def request_response(self):
        return await self.send_and_process_response([])

    async def send_and_process_response(self, messages: list) -> str:
        self.history.extend(messages)
        response = await self.api.request(f"/v1beta/models/{self.model}:generateContent", self.build_request_body_by_history())
        print(json.dumps(response, indent=4))
        if "candidates" not in response or len(response["candidates"]) == 0:
            raise Exception("No candidates in response")

        candidate = response["candidates"][0]
        content = candidate["content"]
        self.history.append(content)
        self.new_messages.append(content)

        # Process message

        response_message = ""

        for part in content["parts"]:
            if "text" in part:
                response_message += part["text"] + "\n"

            if "functionCall" in part:
                function_call = part["functionCall"]
                tool_name = function_call["name"]
                tool_params = function_call["args"]

                for tool in self.tools:
                    if tool.get_name() == tool_name:
                        tool_result = await tool(tool_params)
                        response_message += (await self.send_and_process_response([self.build_function_result_message(tool_result)])) + "\n"

        return response_message
        # raise Exception("Unknown content type")

    def get_new_messages(self):
        n = self.new_messages.copy()
        self.new_messages = []
        return n


async def gemini_generate_one_message(system_prompt: str, user_prompt: str) -> str:
    client = ChatClient(system_instruction=system_prompt)
    return await client.send_message(user_prompt)
