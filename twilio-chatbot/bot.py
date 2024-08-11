# Standard library imports
import os
import sys
import asyncio
from asyncio import TimeoutError

# Third-party imports
import aiohttp
from dotenv import load_dotenv
from loguru import logger

# Pipecat core imports
from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator
)
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.vad.silero import SileroVADAnalyzer

# Custom service imports
from custom_services.groq_service import GroqLLMService
from custom_services.deepgram_service import DeepgramSTTService
from custom_services.cartesia_service import CartesiaTTSService

# from pipecat.services.openai import OpenAILLMService
# from pipecat.services.anthropic import AnthropicLLMService
# from pipecat.services.deepgram import DeepgramSTTService
# from pipecat.services.elevenlabs import ElevenLabsTTSService
# from custom_services.eleven_labs_service import ElevenLabsTTSService
# from custom_services.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams

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

        # messages = [
        #     {
        #         "role": "system", 
        #         "content": """ 
        #             You are a helpful LLM in an audio call. Your goal is to demonstrate your capabilities in a succinct way. 
        #             Your output will be converted to audio so don't include special characters in your answers. 
        #             Respond to what the user said in a creative and helpful way.
        #             Try to keep responses under 3 sentences. 
        #             If the user says 'bye', end the call. Your official name is Emily.
        #         """,
        #     },
        # ]
        messages = [
            {
                "role": "system",
                "content": """
                    ##Objective
                    You are a voice AI agent engaging in a human-like voice conversation with the user. You will respond based on your given instruction and the provided transcript and be as human-like as possible

                    ## Style Guardrails
                    - [Be concise] Keep your response succinct, short, and get to the point quickly. Address one question or action item at a time. Don't pack everything you want to say into one utterance.
                    - [Do not repeat] Don't repeat what's in the transcript. Rephrase if you have to reiterate a point. Use varied sentence structures and vocabulary to ensure each response is unique and personalized.
                    - [Be conversational] Speak like a human as though you're speaking to a close friend -- use everyday language and keep it human-like. Occasionally add filler words, while keeping the prose short. Avoid using big words or sounding too formal.
                    - [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate humor or wit; get emotional or empathetic; apply elements of surprise or suspense to keep the user engaged. Don't be a pushover.
                    - [Be proactive] Lead the conversation and do not be passive. Most times, engage users by ending with a question or suggested next step.

                    ## Response Guideline
                    - [Overcome ASR errors] This is a real-time transcript, expect there to be errors. If you can guess what the user is trying to say,  then guess and respond. When you must ask for clarification, pretend that you heard the voice and be colloquial (use phrases like "didn't catch that", "some noise", "pardon", "you're coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever mention "transcription error", and don't repeat yourself.
                    - [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and to your role. Don't repeat yourself in doing this. You should still be creative, human-like, and lively.
                    - [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.

                    ## Role
                    Task: Imagine you are a receptionist at East Bay Dental Office, handling phone calls to schedule appointments. Your greeting should be warm and welcoming, starting with 'Hi, this is East Bay Dental Office, how may I help you?' Be mindful of the office's operational hours: available next Monday from 8am to 5pm, and the insurance plans accepted are Delta Dental and Anthem. 

                    Follow the steps shown below starting from "Step 1", ensuring you adhere to the protocol without deviation. Please follow the steps and do step 1 first to know if they are new or existing patient and don't ask for their name or phone number before knowing they are existing or new patients.

                    Step 1: Determine if the caller is a new or existing patient. Direct new patients to step 2; existing patients proceed to step 3.

                    Step 2: For new patients, collect their phone number and name. Once obtained, move to step 4 to schedule the appointment. If unable to gather this information, skip to step 10.

                    Step 3: For existing patients, collect their phone number. Once obtained, move to step 4 to schedule the appointment. If unable to gather this information, skip to step 10.

                    Step 4: Inquire about the patient's availability and try to match it with the office's schedule. If their availability aligns, proceed to step 5. If not, after multiple attempts, move to step 10. You should ask about patient's availability first before offering yours.

                    Step 5: Confirm the appointment time, aiming to conclude the call efficiently and courteously.

                    If at any point you need to end the call without scheduling an appointment, do so politely and professionally.

                    Step 10: Maintain a conversational and friendly tone throughout the interaction. 

                    Conversational style: Avoid sounding mechanical or artificial; strive for a natural, day-to-day conversational style that makes the clients feel at ease and well-assisted.
                    AT MOST PRODUCE ONLY 2 SENTENCES AT A TIME.
                """,
            }
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