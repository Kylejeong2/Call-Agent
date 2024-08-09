import aiohttp
import os
import sys
import asyncio
from asyncio import TimeoutError

from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator
)
from pipecat.services.openai import OpenAILLMService
# from pipecat.services.anthropic import AnthropicLLMService
from custom_services.groq_service import GroqLLMService
# from pipecat.services.deepgram import DeepgramSTTService
from custom_services.deepgram_service import DeepgramSTTService
# from pipecat.services.elevenlabs import ElevenLabsTTSService
# from custom_services.eleven_labs_service import ElevenLabsTTSService
from custom_services.cartesia_service import CartesiaTTSService
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
# from custom_services.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.vad.silero import SileroVADAnalyzer
from pipecat.serializers.twilio import TwilioFrameSerializer

from loguru import logger

from dotenv import load_dotenv
load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

async def run_bot(websocket_client, stream_sid): 
    async with aiohttp.ClientSession() as session:
        transport = FastAPIWebsocketTransport(
            websocket=websocket_client,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=TwilioFrameSerializer(stream_sid)
            )
        )

        llm = GroqLLMService(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant"
        )

        stt = DeepgramSTTService(api_key=os.getenv('DEEPGRAM_API_KEY'))

        tts = CartesiaTTSService(
            aiohttp_session=session,
            api_key=os.getenv('CARTESIA_API_KEY'),
            voice_id=os.getenv('CARTESIA_VOICE_ID'),
        )

        messages = [
            {
                "role": "system",
                "content": """ 
                    You are a helpful LLM in an audio call. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way.Try to keep responses under 3 sentences. If the user says 'bye', end the call. Your official name is Emily.
                """,
            },
        ]

        tma_in = LLMUserResponseAggregator(messages)
        tma_out = LLMAssistantResponseAggregator(messages)

        pipeline = Pipeline([
            transport.input(),   # Websocket input from client
            stt,                 # Speech-To-Text
            tma_in,              # User responses
            llm,                 # LLM
            tts,                 # Text-To-Speech
            tma_out,             # LLM responses
            transport.output()   # Websocket output to client
        ])

        task = PipelineTask(pipeline, params=PipelineParams(
            allow_interruptions=True, enable_metrics=True))

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            messages.append(
                {"role": "system", "content": "Please introduce yourself to the user."})
            await task.queue_frames([LLMMessagesFrame(messages)])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            await task.queue_frames([EndFrame()])

        runner = PipelineRunner(handle_sigint=False)

        await runner.run(task)