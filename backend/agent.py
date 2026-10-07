import asyncio
import os
import logging
import httpx
from dotenv import load_dotenv

import edge_tts
import miniaudio
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    stt,
)
from livekit.plugins import deepgram
from phone_parser import parse_phone_number, extract_digits

# Load environment variables
load_dotenv()

# Suppress internal WebRTC byte stream logs
logging.basicConfig(level=logging.INFO)
logging.getLogger("livekit").setLevel(logging.WARNING)
logger = logging.getLogger("phone-parser-agent")

BACKEND_API_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/phone")
PAUSE_TIMEOUT_SECONDS = 4.0


class PhoneCollectorAgent:
    """Manages phone number collection state, explicit confirmation flow, and API submission."""

    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.transcript_tokens = []
        self.silence_task: asyncio.Task | None = None
        self.parsed_phone: str | None = None
        self.detected_language: str = "en"
        self.raw_transcript: str = ""
        self.is_speaking: bool = False
        self.is_confirmed: bool = False
        self.awaiting_user_confirmation: bool = False
        self.audio_source = rtc.AudioSource(24000, 1)
        self.published_track = None

    async def init_audio_track(self):
        """Pre-publishes agent audio track once on room join to eliminate publish latency."""
        track = rtc.LocalAudioTrack.create_audio_track("agent_mic", self.audio_source)
        options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        self.published_track = await self.ctx.room.local_participant.publish_track(track, options)

    def format_digits_for_tts(self, digits: str) -> str:
        """Formats 10 digits with spaces so TTS reads them digit-by-digit."""
        return " . ".join(list(digits))

    def cancel_silence_timer(self):
        """Cancels any pending 4-second silence timeout task."""
        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
            self.silence_task = None

    async def speak(self, text: str, voice: str = "en-IN-NeerjaNeural"):
        """Fast-synthesizes text via edge-tts with +20% rate boost and streams PCM frames immediately."""
        self.is_speaking = True
        try:
            if self.detected_language in ["hi", "mixed"]:
                voice = "hi-IN-SwaraNeural"

            if not self.published_track:
                await self.init_audio_track()

            communicate = edge_tts.Communicate(text, voice, rate="+20%")
            mp3_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_bytes += chunk["data"]

            if not mp3_bytes:
                return

            decoded = miniaudio.decode(mp3_bytes, output_format=miniaudio.SampleFormat.SIGNED16, nchannels=1, sample_rate=24000)
            pcm_data = decoded.samples.tobytes()

            samples_per_frame = 240
            bytes_per_frame = samples_per_frame * 2
            
            for i in range(0, len(pcm_data), bytes_per_frame):
                chunk = pcm_data[i : i + bytes_per_frame]
                if len(chunk) < bytes_per_frame:
                    chunk = chunk + b"\x00" * (bytes_per_frame - len(chunk))
                frame = rtc.AudioFrame(
                    data=chunk, sample_rate=24000, num_channels=1, samples_per_channel=samples_per_frame
                )
                await self.audio_source.capture_frame(frame)
                await asyncio.sleep(0.002)

        except Exception as e:
            logger.error(f"TTS Speech failed: {e}")
        finally:
            self.is_speaking = False

    async def handle_pause_timeout(self):
        """Prompts user if 4 seconds of silence elapse before 10 digits are collected."""
        try:
            await asyncio.sleep(PAUSE_TIMEOUT_SECONDS)
            digits_collected = len(extract_digits(self.raw_transcript))
            if not self.parsed_phone and not self.is_speaking and not self.is_confirmed:
                if digits_collected == 0:
                    logger.info("4-second silence detected on 0 digits.")
                    prompt = (
                        "Main sun raha hoon. Kripya apna 10 digit ka mobile number bataiye."
                        if self.detected_language in ["hi", "mixed"]
                        else "Hello! Please tell me your 10-digit mobile number."
                    )
                    await self.speak(prompt)
                elif digits_collected < 10:
                    logger.info(f"4-second silence detected with {digits_collected} digits. Prompting for full number.")
                    prompt = (
                        f"Mujhe sirf {digits_collected} digits mile. Kripya apna pura number phir se bataiye."
                        if self.detected_language in ["hi", "mixed"]
                        else f"I only got {digits_collected} digits. Could you repeat your full number?"
                    )
                    await self.speak(prompt)
        except asyncio.CancelledError:
            pass

    async def process_text_chunk(self, text: str):
        """Processes incoming STT text chunk with strict conversation state handling."""
        logger.info(f"Received speech chunk: {text}")
        lower_text = text.lower().strip()
        
        # Avoid self-listening loop
        if any(p in lower_text for p in ["i only got", "confirm", "valid mobile number", "please tell me your", "saved", "sun raha hoon", "kripya", "dhanyawad", "mobile number"]):
            return

        # If conversation is already completed, ignore extra speech
        if self.is_confirmed:
            return

        # STATE 2: Awaiting user confirmation after number readback
        if self.awaiting_user_confirmation:
            negative_words = ["no", "not correct", "isn't correct", "is not correct", "not right", "wrong", "galat", "sahi nahi", "nahi", "na", "incorrect"]
            affirmative_words = ["yes", "yeah", "yep", "good", "correct", "right", "haan", "sahi", "thik", "theek", "ok", "okay"]

            is_negative = any(neg in lower_text for neg in negative_words)
            
            if is_negative:
                self.awaiting_user_confirmation = False
                self.parsed_phone = None
                self.transcript_tokens = []
                self.raw_transcript = ""
                reset_msg = (
                    "Kshama kijiye. Kripya apna 10 digit ka mobile number phir se bataiye."
                    if self.detected_language in ["hi", "mixed"]
                    else "I'm sorry. Could you please repeat your 10-digit mobile number?"
                )
                await self.speak(reset_msg)
                return
            elif any(w in lower_text for w in affirmative_words):
                self.is_confirmed = True
                self.awaiting_user_confirmation = False
                thank_msg = (
                    "Dhanyawad! Aapka number save ho gaya hai."
                    if self.detected_language in ["hi", "mixed"]
                    else "Thank you! Your number has been saved."
                )
                await self.speak(thank_msg)
                await self.save_to_backend()
                return

        # STATE 1: Collecting number digits
        self.transcript_tokens.append(text)
        self.raw_transcript = " ".join(self.transcript_tokens)

        num, lang, _ = parse_phone_number(self.raw_transcript)
        self.detected_language = lang

        extracted = extract_digits(self.raw_transcript)

        if num:
            self.parsed_phone = num
            self.cancel_silence_timer()
            formatted_digits = self.format_digits_for_tts(num)
            logger.info(f"SUCCESS: Collected valid 10-digit number: {num}")

            if lang in ["hi", "mixed"]:
                confirm_msg = (
                    f"Main confirm karta hoon — aapka number hai {formatted_digits}. Kya yeh sahi hai?"
                )
            else:
                confirm_msg = (
                    f"Let me confirm — your number is {formatted_digits}. Is that correct?"
                )

            self.awaiting_user_confirmation = True
            await self.speak(confirm_msg)
        elif len(extracted) >= 10 and not num:
            # 10+ digits provided but failed Indian mobile validation (e.g. starts with 1-5)
            self.cancel_silence_timer()
            self.transcript_tokens = []
            self.raw_transcript = ""
            invalid_msg = (
                "Yeh sahi mobile number nahi lag raha hai. Kripya phir se koshish kijiye."
                if lang in ["hi", "mixed"]
                else "That doesn't look like a valid mobile number. Please try again."
            )
            await self.speak(invalid_msg)
        else:
            logger.info(f"Current partial transcript: '{self.raw_transcript}' (Digits so far: {len(extracted)})")
            self.cancel_silence_timer()
            self.silence_task = asyncio.create_task(self.handle_pause_timeout())

    async def save_to_backend(self):
        """Posts validated record to SQLite backend API."""
        if not self.parsed_phone:
            return
        payload = {
            "rawTranscript": self.raw_transcript,
            "parsedNumber": self.parsed_phone,
            "language": self.detected_language,
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(BACKEND_API_URL, json=payload, timeout=5.0)
                if res.status_code == 201:
                    logger.info(f"Successfully saved to database: {self.parsed_phone}")
                elif res.status_code == 400:
                    logger.warning(f"Duplicate entry rejected by database: {self.parsed_phone}")
        except Exception as e:
            logger.error(f"Failed posting record to backend API: {e}")


async def entrypoint(ctx: JobContext):
    """Entrypoint triggered when agent worker joins LiveKit room session."""
    logger.info("Agent joining LiveKit room session...")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    collector = PhoneCollectorAgent(ctx)
    await collector.init_audio_track()

    stt_plugin = deepgram.STT(model="nova-2-general", language="hi", smart_format=True, numerals=True, interim_results=False)

    asyncio.create_task(collector.speak("Hello! Please tell me your 10-digit mobile number."))

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        if participant.identity == ctx.room.local_participant.identity:
            return

        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"Subscribed to participant microphone track: {participant.identity}")
            stt_stream = stt_plugin.stream()

            async def send_audio_to_stt():
                audio_stream = rtc.AudioStream(track)
                async for event in audio_stream:
                    if not collector.is_speaking and not collector.is_confirmed:
                        stt_stream.push_frame(event.frame)

            async def listen_stt_events():
                async for ev in stt_stream:
                    if ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                        text = ev.alternatives[0].text if ev.alternatives else ""
                        if text.strip():
                            await collector.process_text_chunk(text)

            asyncio.create_task(send_audio_to_stt())
            asyncio.create_task(listen_stt_events())


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))