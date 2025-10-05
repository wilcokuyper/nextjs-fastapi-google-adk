import json
import uuid
from typing import Any, AsyncGenerator, Dict, Sequence

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.agents import RunConfig
from google.adk.agents.run_config import StreamingMode

from agents.chat_agent import chat_agent

load_dotenv()
app = FastAPI()

session_service = InMemorySessionService()

# Instantiate the runner once so every request shares the same in-memory session store.
runner = Runner(app_name="chat-agent", agent=chat_agent, session_service=session_service)
config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    max_llm_calls=200
)


def _message_text(message: dict) -> str:
    """Extract plain text from UI message structures."""
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [
            part.get("text")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        if texts:
            return "\n".join(texts)

    parts = message.get("parts")
    if isinstance(parts, list):
        texts = [
            part.get("text")
            for part in parts
            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str)
        ]
        if texts:
            return "\n".join(texts)

    return ""


def _extract_latest_user_message(messages: Sequence[dict]) -> str:
    """Return the most recent user message content from the UI payload."""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            candidate = _message_text(message)
            if candidate:
                return candidate
    return ""


def _sse_payload(data: Dict[str, Any]) -> bytes:
    """Encode a single SSE event chunk."""
    return f"data: {json.dumps(data)}\n\n".encode("utf-8")


@app.post("/chat")
async def chat(req: Request) -> StreamingResponse:
    body = await req.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body")

    messages = body.get("messages") or []
    if not isinstance(messages, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="messages must be a list")

    user_id = body.get("user_id") or "anonymous"

    user_text = _extract_latest_user_message(messages)
    if not user_text:
        fallback = body.get("input") or body.get("message") or ""
        user_text = fallback if isinstance(fallback, str) else ""
    user_text = user_text.strip()
    if not user_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user message provided")

    session_id = body.get("session_id") or body.get("sessionId")
    session = None
    if session_id:
        session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )

    if session is None:
        session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        session_id = session.id

    new_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_text)],
    )

    async def event_stream() -> AsyncGenerator[bytes, None]:
        message_id = str(uuid.uuid4())
        text_id = "0"
        text_started = False

        # Surface the session ID up front so the UI can reuse it on the next turn.
        yield _sse_payload({
            "type": "start",
            "messageId": message_id,
            "messageMetadata": {"sessionId": session_id},
        })

        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
                run_config=config
            ):
                if event.error_message:
                    yield _sse_payload({"type": "error", "errorText": event.error_message})
                    break
                
                if event.content:
                    text_parts = [
                        part.text for part in (event.content.parts or []) if getattr(part, "text", None)
                    ]
                    print(text_parts)
                    if text_parts:
                        if not text_started:
                            print('text-start')
                            yield _sse_payload({"type": "text-start", "id": text_id})
                            text_started = True

                        print("text-delta")
                        for text_part in text_parts:
                            yield _sse_payload({
                                "type": "text-delta",
                                "id": text_id,
                                "delta": text_part,
                            })

                if event.turn_complete and text_started:
                    yield _sse_payload({"type": "text-end", "id": text_id})
                    text_started = False

            if text_started:
                yield _sse_payload({"type": "text-end", "id": text_id})
        except Exception as exc:  # pragma: no cover - defensive guard for runtime issues
            yield _sse_payload({"type": "error", "errorText": str(exc)})
        finally:
            yield _sse_payload({
                "type": "finish",
                "messageMetadata": {"sessionId": session_id},
            })
            yield b"data: [DONE]\n\n"

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.headers["cache-control"] = "no-cache"
    response.headers["x-accel-buffering"] = "no"
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["x-session-id"] = session_id
    return response


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await runner.close()
