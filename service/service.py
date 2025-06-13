import base64
import json
import logging
from typing import AsyncGenerator, Dict
from uuid import uuid4

from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events import Event
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from manager_agent.agent import root_agent
from models.exception import InteropAEException
from models.request import UserRequest

logger = logging.getLogger(__name__)

APP_NAME = "ADK_MCP_APP"
session_id = uuid4().hex


async def start_agent_session(user_id, is_audio=False):
    """Starts an agent session"""

    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )

    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    modality = "AUDIO" if is_audio else "TEXT"
    run_config = RunConfig(response_modalities=[modality])

    live_request_queue = LiveRequestQueue()

    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue


async def agent_to_client_sse(live_events: AsyncGenerator[Event, None]):
    """Agent to client communication via SSE"""
    async for event in live_events:
        # If the turn complete or interrupted, send it
        if event.turn_complete or event.interrupted:
            message = {
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }
            yield f"data: {json.dumps(message)}\n\n"
            logger.info(f"[AGENT TO CLIENT]: {message}")
            continue

        # Read the Content and its first Part
        part: Part = event.content and event.content.parts and event.content.parts[0]
        if not part:
            continue

        # If it's audio, send Base64 encoded audio data
        is_audio = part.inline_data and part.inline_data.mime_type.startswith(
            "audio/pcm"
        )
        if is_audio:
            audio_data = part.inline_data and part.inline_data.data
            if audio_data:
                message = {
                    "mime_type": "audio/pcm",
                    "data": base64.b64encode(audio_data).decode("ascii"),
                }
                yield f"data: {json.dumps(message)}\n\n"
                logger.info(f"[AGENT --> CLIENT]: audio/pcm: {len(audio_data)} bytes.")
                continue

        # If it's text and a parial text, send it
        if part.text and event.partial:
            message = {"mime_type": "text/plain", "data": part.text}
            yield f"data: {json.dumps(message)}\n\n"
            logger.info(f"[AGENT --> CLIENT]: text/plain: {message}")


def cleanup(
    user_id: str,
    active_sessions: Dict[str, Event],
    live_request_queue: LiveRequestQueue,
):
    live_request_queue.close()
    if user_id in active_sessions:
        del active_sessions[user_id]
    logger.info(f"Client #{user_id} disconnected from SSE")


async def event_generator(
    user_id: str,
    active_sessions: Dict[str, Event],
    live_events: AsyncGenerator[Event, None],
    live_request_queue: LiveRequestQueue,
):
    try:
        async for data in agent_to_client_sse(live_events):
            yield data
    except Exception as e:
        logger.error(f"\t ===== Error in SSE stream =====\nReason: {e}")
        raise InteropAEException(message=str(e), status_code=500)
    finally:
        cleanup(user_id, active_sessions, live_request_queue)


async def send_message_non_streaming(user_id: str, request: UserRequest):
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        memory_service=InMemoryMemoryService(),
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
    )
    session = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await runner.session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id, state={}
        )
    content = Content(role="user", parts=[Part.from_text(text=request.query)])
    events = list(
        runner.run(user_id=user_id, session_id=session.id, new_message=content)
    )
    if not events or not events[-1].content or not events[-1].content.parts:
        return {"response": "No response from agent", "type": "text"}
    return {"response": "\n".join(p.text for p in events[-1].content.parts if p.text), "type": "text"}
