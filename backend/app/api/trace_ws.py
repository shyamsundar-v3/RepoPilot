import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.orchestration.trace_bus import trace_bus

router = APIRouter()


@router.websocket("/ws/trace/{job_id}")
async def trace_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    queue = trace_bus.subscribe(job_id)
    try:
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=300)
            await websocket.send_text(event.model_dump_json())
            if event.type.value in ("done", "error"):
                break
    except (asyncio.TimeoutError, WebSocketDisconnect):
        pass
    finally:
        trace_bus.unsubscribe(job_id, queue)
        try:
            await websocket.close()
        except Exception:
            pass
