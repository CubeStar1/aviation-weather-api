from flask import Blueprint, request, Response, stream_with_context
import os
import json
import asyncio
import websockets
from dotenv import load_dotenv

load_dotenv()

gemini_live = Blueprint('gemini_live', __name__)

class GeminiConnection:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = "gemini-2.0-flash-exp"
        self.uri = (
            "wss://generativelanguage.googleapis.com/ws/"
            "google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
            f"?key={self.api_key}"
        )
        self.ws = None
        self.config = None

    async def connect(self):
        """Initialize connection to Gemini"""
        self.ws = await websockets.connect(
            self.uri,
            extra_headers={"Content-Type": "application/json"}
        )

        if not self.config:
            raise ValueError("Configuration must be set before connecting")

        # Send initial setup message with configuration
        setup_message = {
            "setup": {
                "model": f"models/{self.model}",
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": self.config["voice"]
                            }
                        }
                    }
                },
                "system_instruction": {
                    "parts": [
                        {
                            "text": self.config["systemPrompt"]
                        }
                    ]
                }
            }
        }
        await self.ws.send(json.dumps(setup_message))
        return await self.ws.recv()

    def set_config(self, config):
        """Set configuration for the connection"""
        self.config = config

    async def send_message(self, message_type, data):
        """Send a message to Gemini based on type"""
        if message_type == "audio":
            await self.send_audio(data)
        elif message_type == "image":
            await self.send_image(data)
        elif message_type == "text":
            await self.send_text(data)

    async def send_audio(self, audio_data: str):
        """Send audio data to Gemini"""
        message = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "data": audio_data,
                        "mime_type": "audio/pcm"
                    }
                ]
            }
        }
        await self.ws.send(json.dumps(message))

    async def send_image(self, image_data: str):
        """Send image data to Gemini"""
        message = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "data": image_data,
                        "mime_type": "image/jpeg"
                    }
                ]
            }
        }
        await self.ws.send(json.dumps(message))

    async def send_text(self, text: str):
        """Send text message to Gemini"""
        message = {
            "client_content": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [{"text": text}]
                    }
                ],
                "turn_complete": True
            }
        }
        await self.ws.send(json.dumps(message))

    async def receive(self):
        """Receive message from Gemini"""
        return await self.ws.recv()

    async def close(self):
        """Close the connection"""
        if self.ws:
            await self.ws.close()

async def process_gemini_stream(gemini, request_data):
    """Process the Gemini stream and yield responses"""
    try:
        # Set configuration
        gemini.set_config(request_data.get("config", {}))
        
        # Connect to Gemini
        await gemini.connect()

        # Send the initial message
        if "message" in request_data:
            await gemini.send_message(
                request_data["type"],
                request_data["message"]
            )

        # Receive and yield responses
        while True:
            response = await gemini.receive()
            response_data = json.loads(response)

            # Process server content
            if "serverContent" in response_data:
                parts = response_data["serverContent"].get("modelTurn", {}).get("parts", [])
                
                for part in parts:
                    if "inlineData" in part:
                        yield json.dumps({
                            "type": "audio",
                            "data": part["inlineData"]["data"]
                        }) + "\n"
                    elif "text" in part:
                        yield json.dumps({
                            "type": "text",
                            "text": part["text"]
                        }) + "\n"

                # Handle turn completion
                if response_data["serverContent"].get("turnComplete"):
                    yield json.dumps({
                        "type": "turn_complete",
                        "data": True
                    }) + "\n"
                    break

    except Exception as e:
        yield json.dumps({
            "type": "error",
            "message": str(e)
        }) + "\n"
    finally:
        await gemini.close()

@gemini_live.route('/stream', methods=['POST'])
def gemini_stream():
    """Flask endpoint for streaming Gemini responses"""
    request_data = request.get_json()

    def generate():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        gemini = GeminiConnection()
        
        try:
            for response in loop.run_until_complete(process_gemini_stream(gemini, request_data)):
                yield response
        finally:
            loop.close()

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    ) 