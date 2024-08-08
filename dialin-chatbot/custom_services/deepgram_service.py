#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import aiohttp
import time

from typing import AsyncGenerator

from pipecat.frames.frames import (
    AudioRawFrame,
    CancelFrame,
    EndFrame,
    ErrorFrame,
    Frame,
    InterimTranscriptionFrame,
    StartFrame,
    SystemFrame,
    TranscriptionFrame)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.ai_services import AsyncAIService, TTSService
from pipecat.utils.time import time_now_iso8601

from loguru import logger
# See .env.example for Deepgram configuration needed
try:
    from deepgram import (
        DeepgramClient,
        DeepgramClientOptions,
        LiveTranscriptionEvents,
        LiveOptions,
    )
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error(
        "In order to use Deepgram, you need to `pip install pipecat-ai[deepgram]`. Also, set `DEEPGRAM_API_KEY` environment variable.")
    raise Exception(f"Missing module: {e}")


class DeepgramTTSService(TTSService):

    def __init__(
            self,
            *,
            aiohttp_session: aiohttp.ClientSession,
            api_key: str,
            voice: str = "aura-helios-en",
            base_url: str = "https://api.deepgram.com/v1/speak",
            **kwargs):
        super().__init__(**kwargs)

        self._voice = voice
        self._api_key = api_key
        self._aiohttp_session = aiohttp_session
        self._base_url = base_url

    def can_generate_metrics(self) -> bool:
        return True

    async def set_voice(self, voice: str):
        logger.debug(f"Switching TTS voice to: [{voice}]")
        self._voice = voice

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        logger.debug(f"Generating TTS: [{text}]")

        base_url = self._base_url
        request_url = f"{base_url}?model={self._voice}&encoding=linear16&container=none&sample_rate=16000"
        headers = {"authorization": f"token {self._api_key}"}
        body = {"text": text}

        try:
            await self.start_ttfb_metrics()
            async with self._aiohttp_session.post(request_url, headers=headers, json=body) as r:
                if r.status != 200:
                    response_text = await r.text()
                    # If we get a a "Bad Request: Input is unutterable", just print out a debug log.
                    # All other unsuccesful requests should emit an error frame. If not specifically
                    # handled by the running PipelineTask, the ErrorFrame will cancel the task.
                    if "unutterable" in response_text:
                        logger.debug(f"Unutterable text: [{text}]")
                        return

                    logger.error(
                        f"{self} error getting audio (status: {r.status}, error: {response_text})")
                    yield ErrorFrame(f"Error getting audio (status: {r.status}, error: {response_text})")
                    return

                async for data in r.content:
                    await self.stop_ttfb_metrics()
                    frame = AudioRawFrame(audio=data, sample_rate=16000, num_channels=1)
                    yield frame
        except Exception as e:
            logger.exception(f"{self} exception: {e}")


class DeepgramSTTService(AsyncAIService):
    def __init__(self,
                 *,
                 api_key: str,
                 url: str = "",
                 live_options: LiveOptions = LiveOptions(
                     encoding="linear16",
                     language="en-US",
                     model="nova-2-phonecall",
                     sample_rate=16000,
                     channels=1,
                     interim_results=True,
                     smart_format=True,
                 ),
                 **kwargs):
        super().__init__(**kwargs)

        self._live_options = live_options

        self._client = DeepgramClient(
            api_key, config=DeepgramClientOptions(url=url, options={"keepalive": "true"}))
        self._connection = self._client.listen.asynclive.v("1")
        self._connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
        
    def can_generate_metrics(self) -> bool:
        return True

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, SystemFrame):
            await self.push_frame(frame, direction)
        elif isinstance(frame, AudioRawFrame):
            await self.start_ttfb_metrics()
            await self._connection.send(frame.audio)
        else:
            await self.queue_frame(frame, direction)

    async def start(self, frame: StartFrame):
        if await self._connection.start(self._live_options):
            logger.debug(f"{self}: Connected to Deepgram")
        else:
            logger.error(f"{self}: Unable to connect to Deepgram")

    async def stop(self, frame: EndFrame):
        await self._connection.finish()
        await self.stop_all_metrics()

    async def cancel(self, frame: CancelFrame):
        await self._connection.finish()
        await self.stop_all_metrics()

    async def _on_message(self, *args, **kwargs):
        result = kwargs["result"]
        is_final = result.is_final
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0:
            await self.stop_ttfb_metrics()
            if is_final:
                await self.queue_frame(TranscriptionFrame(transcript, "", time_now_iso8601()))
            else:
                await self.queue_frame(InterimTranscriptionFrame(transcript, "", time_now_iso8601()))
