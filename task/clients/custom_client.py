import json
import aiohttp
import requests

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role


class CustomDialClient(BaseClient):
    _endpoint: str

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._endpoint = DIAL_ENDPOINT + f"/openai/deployments/{deployment_name}/chat/completions"

    def get_completion(self, messages: list[Message]) -> Message:
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        request_data = {
            "messages": [msg.to_dict() for msg in messages]
        }

        response = requests.post(
            url=self._endpoint,
            headers=headers,
            json=request_data
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        response_json = response.json()
        content = response_json["choices"][0]["message"]["content"]
        print(content)

        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json"
        }

        request_data = {
            "stream": True,
            "messages": [msg.to_dict() for msg in messages]
        }

        contents = []

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self._endpoint,
                headers=headers,
                json=request_data
            ) as response:
                async for line in response.content:
                    chunk_str = line.decode("utf-8").strip()
                    
                    if not chunk_str:
                        continue
                    
                    content_snippet = self._get_content_snippet(chunk_str)
                    if content_snippet:
                        print(content_snippet, end="", flush=True)
                        contents.append(content_snippet)

        print()

        return Message(role=Role.AI, content="".join(contents))

    def _get_content_snippet(self, chunk: str) -> str | None:
        if not chunk.startswith("data: "):
            return None

        json_str = chunk[6:]

        if json_str == "[DONE]":
            return None

        try:
            data = json.loads(json_str)
            choices = data.get("choices", [])
            if choices and "delta" in choices[0]:
                return choices[0]["delta"].get("content")
        except json.JSONDecodeError:
            return None

        return None

