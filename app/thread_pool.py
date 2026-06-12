import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any

logger = logging.getLogger(__name__)

# Pool of 5 background threads for notification generation
_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="notification_worker")

# Semaphore to enforce max concurrent in-flight tasks (matches pool size)
_semaphore = threading.Semaphore(5)


def submit_task(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:
    """
    Submit a callable to the background thread pool.

    Returns a concurrent.futures.Future so callers can optionally
    inspect completion or handle exceptions.

    Raises:
        RuntimeError: If the pool is saturated (all workers busy).
    """
    if not _semaphore.acquire(blocking=False):
        logger.error(
            "module=app.thread_pool method=submit_task message=All workers busy, rejecting task"
        )
        raise RuntimeError(
            "Background worker pool is saturated. Please try again later."
        )

    logger.info(
        "module=app.thread_pool method=submit_task message=Submitting task to background thread pool"
    )

    future = _executor.submit(fn, *args, **kwargs)

    def _release_on_done(f: Future) -> None:
        _semaphore.release()
        exc = f.exception()
        if exc:
            logger.error(
                f"module=app.thread_pool method=submit_task message=Background task failed: {str(exc)}"
            )

    future.add_done_callback(_release_on_done)
    return future


def shutdown(wait: bool = True) -> None:
    """
    Gracefully shut down the thread pool.

    Call during application shutdown to avoid orphaned threads.
    """
    logger.info(
        "module=app.thread_pool method=shutdown message=Shutting down background thread pool"
    )
    _executor.shutdown(wait=wait)
