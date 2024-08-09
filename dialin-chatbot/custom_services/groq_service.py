#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

# Edited by Kyle Jeong

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

try:
    from groq import AsyncGroq
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error(
        "In order to use Groq, you need to `pip install groq`. Also, set `GROQ_API_KEY` environment variable.")
    raise Exception(f"Missing module: {e}")

class GroqLLMService(LLMService):
    def __init__(
            self,
            *,
            api_key: str,
            model: str = "llama3-8b-8192",
            max_tokens: int = 1024):
        super().__init__()
        self._client = AsyncGroq(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
    
    def can_generate_metrics(self) -> bool:
        return True

    def _get_messages_from_openai_context(
            self, context: OpenAILLMContext):
        openai_messages = context.get_messages()
        groq_messages = []

        for message in openai_messages:
            role = message["role"]
            text = message["content"]
            if role == "system":
                role = "user"
            if message.get("mime_type") == "image/jpeg":
                # vision frame
                encoded_image = base64.b64encode(message["data"].getvalue()).decode("utf-8")
                groq_messages.append({
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
                if role == "user" and len(groq_messages) > 1:
                    last_message = groq_messages[-1]
                    if last_message["role"] == "user":
                        groq_messages = groq_messages[:-1]
                        content = last_message["content"]
                        groq_messages.append(
                            {"role": "user", "content": f"Sorry, I just asked you about [{content}] but now I would like to know [{text}]."})
                    else:
                        groq_messages.append({"role": role, "content": text})
                else:
                    groq_messages.append({"role": role, "content": text})

        return groq_messages

    async def _process_context(self, context: OpenAILLMContext):
        await self.push_frame(LLMFullResponseStartFrame())
        try:
            logger.debug(f"Generating chat: {context.get_messages_json()}")

            messages = self._get_messages_from_openai_context(context)

            await self.start_ttfb_metrics()

            response = await self._client.chat.completions.create(
                messages=messages,
                model=self._model,
                max_tokens=self._max_tokens,
                stream=True
            )

            await self.stop_ttfb_metrics()

            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    await self.push_frame(TextFrame(chunk.choices[0].delta.content))

        except Exception as e:
            logger.exception(f"{self} exception: {e}")
        finally:
            await self.push_frame(LLMFullResponseEndFrame())
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        context = None

        if isinstance(frame, OpenAILLMContextFrame):
            context: OpenAILLMContext = frame.context
        elif isinstance(frame, LLMMessagesFrame):
            context = OpenAILLMContext.from_messages(frame.messages)
        elif isinstance(frame, VisionImageRawFrame):
            context = OpenAILLMContext.from_image_frame(frame)
        elif isinstance(frame, LLMModelUpdateFrame):
            logger.debug(f"Switching LLM model to: [{frame.model}]")
            self._model = frame.model
        else:
            await self.push_frame(frame, direction)

        if context:
            await self._process_context(context)