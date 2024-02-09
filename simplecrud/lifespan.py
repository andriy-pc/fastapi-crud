from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from simplecrud.database.database_setup import generate_async_engine
from simplecrud.jobsimulation.job_processor import generate_job_processor


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with generate_async_engine(), generate_job_processor():
        yield
