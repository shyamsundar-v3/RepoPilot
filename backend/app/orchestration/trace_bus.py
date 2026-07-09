import asyncio
import time
from collections import defaultdict

from app.models.schemas import TraceEvent, TraceEventType


class TraceBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, job_id: str) -> asyncio.Queue:
        self._loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[job_id].append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        if job_id in self._subscribers:
            self._subscribers[job_id] = [q for q in self._subscribers[job_id] if q is not queue]
            if not self._subscribers[job_id]:
                del self._subscribers[job_id]

    def emit(self, job_id: str, event: TraceEvent):
        event.timestamp = event.timestamp or time.time()
        for queue in self._subscribers.get(job_id, []):
            if self._loop is not None:
                self._loop.call_soon_threadsafe(queue.put_nowait, event)
            else:
                queue.put_nowait(event)

    def emit_simple(self, job_id: str, event_type: str, **kwargs):
        self.emit(job_id, TraceEvent(type=TraceEventType(event_type), **kwargs))


trace_bus = TraceBus()
