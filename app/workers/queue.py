import asyncio
from typing import Any, Callable, Coroutine, Dict, Optional
from app.core.logging import logger


class JobQueue:
    """
    Asynchronous in-memory job queue with worker background loop.
    Ensures decoupled, non-blocking webhook processing.
    """
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._handlers: Dict[str, Callable[..., Coroutine[Any, Any, None]]] = {}
        self._running = False

    def register_handler(self, task_name: str, handler: Callable[..., Coroutine[Any, Any, None]]):
        self._handlers[task_name] = handler

    async def enqueue(self, task_name: str, **kwargs) -> None:
        await self._queue.put({"task_name": task_name, "kwargs": kwargs})
        logger.debug(f"[JobQueue] Enqueued task '{task_name}', queue size: {self._queue.qsize()}")

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("[JobQueue] Background worker started.")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("[JobQueue] Background worker stopped.")

    async def _process_queue(self) -> None:
        while self._running:
            try:
                item = await self._queue.get()
                task_name = item.get("task_name")
                kwargs = item.get("kwargs", {})
                handler = self._handlers.get(task_name)

                if handler:
                    try:
                        logger.info(f"[JobQueue] Executing worker task '{task_name}'")
                        await handler(**kwargs)
                    except Exception as exc:
                        logger.error(f"[JobQueue] Error executing task '{task_name}': {str(exc)}", exc_info=True)
                else:
                    logger.warning(f"[JobQueue] No handler registered for task '{task_name}'")

                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[JobQueue] Unexpected error in worker loop: {str(e)}", exc_info=True)


# Global job queue instance
job_queue = JobQueue()
