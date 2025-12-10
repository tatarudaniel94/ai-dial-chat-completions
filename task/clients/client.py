from aidial_client import Dial, AsyncDial

from task.clients.base import BaseClient
from task.constants import DIAL_ENDPOINT
from task.models.message import Message
from task.models.role import Role

class DialClient(BaseClient):

    def __init__(self, deployment_name: str):
        super().__init__(deployment_name)
        self._client = Dial(dial_url=DIAL_ENDPOINT, api_key=self._api_key)
        self._async_client = AsyncDial(dial_url=DIAL_ENDPOINT, api_key=self._api_key)

    def get_completion(self, messages: list[Message]) -> Message:
        messages_dict = [msg.to_dict() for msg in messages]
        
        response = self._client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=messages_dict
        )
        
        if not response.choices:
            raise Exception("No choices in response found")
        
        content = response.choices[0].message.content
        print(content)
        
        return Message(role=Role.AI, content=content)

    async def stream_completion(self, messages: list[Message]) -> Message:
        messages_dict = [msg.to_dict() for msg in messages]
        
        chunks = await self._async_client.chat.completions.create(
            deployment_name=self._deployment_name,
            messages=messages_dict,
            stream=True
        )
        
        contents = []
        
        async for chunk in chunks:
            if chunk.choices and chunk.choices[0].delta.content:
                content_piece = chunk.choices[0].delta.content
                print(content_piece, end="", flush=True)
                contents.append(content_piece)
        
        print()
        
        return Message(role=Role.AI, content="".join(contents))
