import asyncio
import logging
import random
import time
from asyncio import Task
from contextlib import asynccontextmanager
from secrets import token_urlsafe
from typing import AsyncGenerator, Any, Set

from pydantic import BaseModel

log = logging.getLogger(__name__)

_shutdown: bool = False
_shutdown_start_time: float
_job_handler_tasks: Set[asyncio.Task[None]] = set()


class ShutdownInterrupt(Exception):
    "Raised when the _shutdown flag is found to be True"
    pass


class PrintJob(BaseModel):
    id: str
    name: str = "Simple class to simulate some job"

    def __str__(self) -> str:
        return f"PrintJob(id={self.id!r}, name={self.name!r})"


async def print_job_processor() -> None:
    while not _shutdown:
        try:
            global _job_handler_tasks
            print_job = await find_print_job()
            if print_job is not None:
                log.info(f"Found new job to process. Currently running {len(_job_handler_tasks)} jobs")
                job_handler_task = asyncio.create_task(
                    print_job_handler(print_job)
                )
                _job_handler_tasks.add(job_handler_task)
                job_handler_task.add_done_callback(print_job_post_process)
            else:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            log.info("job_processor: cancelled")
            raise
        except Exception:
            await asyncio.sleep(5)
    log.info("job_processor shutdown")


async def find_print_job() -> PrintJob:
    job: PrintJob | None = None
    if (len(_job_handler_tasks) == 0
            or (len(_job_handler_tasks) < 5 and random.randint(0, 1000) % 17 == 0)):
        log.info("Creating job...")
        job = PrintJob(id=token_urlsafe(16))

    return job


async def print_job_handler(job: PrintJob) -> None:
    log.info(f"Processing job: {job}")
    start_time = time.perf_counter()
    await asyncio.sleep(random.randint(0, 120))
    end_time = time.perf_counter()
    log.info(f"Job finished successfully in {end_time - start_time} seconds. Job: {job}")


def print_job_post_process(task: asyncio.Task[None]) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        log.debug(f"Task cancelled: {task.get_name()}")
    except ShutdownInterrupt:
        pass
    except Exception:
        log.exception(f"Exception raised by task: {task.get_name()}")
    _job_handler_tasks.discard(task)

@asynccontextmanager
async def generate_job_processor() -> AsyncGenerator[None, None]:
    print_job_processor_task = asyncio.create_task(print_job_processor())
    try:
        yield
    finally:
        log.info("Starting shutdown")
        global _shutdown, _shutdown_start_time
        _shutdown_start_time = time.perf_counter()
        _shutdown = True
        while (
                not print_job_processor_task.done()
        ):
            if time.perf_counter() - _shutdown_start_time > 15.0:
                log.info("Graceful shutdown wait time exceeded, cancelling tasks")
                break
            await asyncio.sleep(1)

        if not print_job_processor_task.done():
            log.info("cancelling print_job_processor_task")
            await cancel_job_processor(print_job_processor_task)


async def cancel_job_processor(job_processor_task: Task[Any]) -> None:
    job_processor_task.cancel()
    try:
        await job_processor_task
    except asyncio.CancelledError:
        log.info("job_processor_task is cancelled")
    except ShutdownInterrupt:
        pass
    except Exception:
        log.exception("job_processor_task cancelled with an exception")
