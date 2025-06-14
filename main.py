import base64
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from google.adk.agents import LiveRequestQueue
from google.genai.types import Blob, Content, Part

from decorator.decorator import token_required
from models.exception import InteropAEException
from models.request import UserRequest
from models.response import ServerResponse, StatusMessage
from service import service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    server_domain = os.getenv("SERVER_DOMAIN") or "http://localhost"
    credentials = requests.get(f"{server_domain}:5002/credentials").json()
    for creds in credentials["data"]:
        os.environ[creds] = credentials["data"].get(creds)
    load_dotenv()
    yield


app = FastAPI()
active_sessions: Dict[str, LiveRequestQueue] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InteropAEException)
async def handle_exception(request: Request, exception: InteropAEException):
    return JSONResponse(
        content=ServerResponse(
            data=None, status=StatusMessage.ERROR, message=exception.message
        ).model_dump(),
        status_code=exception.status_code,
    )


@app.get("/events/{user_id}")
async def sse_connection(user_id: str, is_audio: bool = False):
    """SSE endpoint for agent to client communication"""
    # Start agent session
    live_events, live_request_queue = await service.start_agent_session(
        user_id, is_audio
    )

    active_sessions[user_id] = live_request_queue

    logger.info(f"User <{user_id}> connected via SSE, audio mode: {is_audio}")

    return StreamingResponse(
        service.event_generator(
            user_id, active_sessions, live_events, live_request_queue
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@app.post("/response")
@token_required
async def send_message_non_streaming(request: Request, user_request: UserRequest):
    user_id = str(request.state.user.get("id"))
    response = await service.send_message_non_streaming(user_id, user_request)
    return JSONResponse(
        content=ServerResponse(
            data=response,
            status=StatusMessage.OK,
            message="Agent responded successfully",
        ).model_dump(by_alias=True)
    )


@app.post("/response-streaming/{user_id}")
async def send_message_streaming(user_id: str, request: UserRequest):

    live_request_queue = active_sessions.get(user_id)
    if not live_request_queue:
        raise InteropAEException(message="Session not found", status_code=404)

    mime_type = "text/plain"
    data = request.message

    if mime_type == "text/plain":
        content = Content(role="user", parts=[Part.from_text(text=data)])
        live_request_queue.send_content(content=content)
        logger.info(f"[CLIENT --> AGENT]: {data}")
    elif mime_type == "audio/pcm":
        decoded_data = base64.b64decode(data)
        live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
        logger.info(f"[CLIENT --> AGENT]: audio/pcm: {len(decoded_data)} bytes")
    else:
        raise InteropAEException(
            message=f"Mime type not supported: {mime_type}", status_code=400
        )

    return JSONResponse(
        content=ServerResponse(
            data="Message sent successfully, wait for response stream at `GET /events/{user_id}` endpoint",
            status=StatusMessage.OK,
            message="Message sent successfully",
        ).model_dump(by_alias=True)
    )
