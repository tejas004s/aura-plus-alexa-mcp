"""
transports.py - Streamable HTTP & SSE Transport Implementation for MCP Spec 2025-11-25+

Manages active client sessions, bidirectional message routing, and chunked SSE streams.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import Request
from sse_starlette.sse import ServerSentEvent


class StreamableHTTPTransport:
    """Handles MCP sessions and Server-Sent Events over Streamable HTTP."""

    def __init__(self):
        # session_id -> asyncio.Queue of messages to send to the client
        self._sessions: Dict[str, asyncio.Queue] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = asyncio.Queue()
        return session_id

    def remove_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    async def broadcast_event(self, session_id: str, event_type: str, data: Any) -> bool:
        if session_id in self._sessions:
            payload = json.dumps(data) if not isinstance(data, str) else data
            await self._sessions[session_id].put(ServerSentEvent(event=event_type, data=payload))
            return True
        return False

    async def sse_event_stream(self, session_id: str, request: Request) -> AsyncGenerator[ServerSentEvent, None]:
        """Generator that streams events to the connected HTTP client."""
        # Yield the initial endpoint URI as required by MCP SSE specification
        endpoint_url = f"/mcp/message?session_id={session_id}"
        yield ServerSentEvent(event="endpoint", data=endpoint_url)

        queue = self._sessions.get(session_id)
        if not queue:
            return

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Wait for next event with a periodic keepalive ping
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event
                except asyncio.TimeoutError:
                    yield ServerSentEvent(event="ping", data="keepalive")
        finally:
            self.remove_session(session_id)


transport_manager = StreamableHTTPTransport()
