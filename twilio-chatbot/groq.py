# BSD 2-Clause License

import base64

from pipecat.frames.frames import (
    Frame,
    LLMModelUpdateFrame,
    TextFrame,
    VisionImageRawFrame,
    LLMMessagesFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.ai_services import LLMService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext, OpenAILLMContextFrame

from loguru import logger

from pipecat.services.ai_services import AIService

class GroqLLMService(AIService):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def _get_messages_from_openai_context(
            self, context: OpenAILLMContext):
        openai_messages = context.get_messages()
        anthropic_messages = []

        for message in openai_messages:
            role = message["role"]
            text = message["content"]
            if role == "system":
                role = "user"
            if message.get("mime_type") == "image/jpeg":
                # vision frame
                encoded_image = base64.b64encode(message["data"].getvalue()).decode("utf-8")
                anthropic_messages.append({
                    "role": role,
                    "content": [{
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": message.get("mime_type"),
                            "data": encoded_image,
                        }
                    }, {
                        "type": "text",
                        "text": text
                    }]
                })
            else:
                # Text frame. Anthropic needs the roles to alternate. This will
                # cause an issue with interruptions. So, if we detect we are the
                # ones asking again it probably means we were interrupted.
                if role == "user" and len(anthropic_messages) > 1:
                    last_message = anthropic_messages[-1]
                    if last_message["role"] == "user":
                        anthropic_messages = anthropic_messages[:-1]
                        content = last_message["content"]
                        anthropic_messages.append(
                            {"role": "user", "content": f"Sorry, I just asked you about [{content}] but now I would like to know [{text}]."})
                    else:
                        anthropic_messages.append({"role": role, "content": text})
                else:
                    anthropic_messages.append({"role": role, "content": text})

        return anthropic_messages