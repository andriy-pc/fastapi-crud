import logging
import os

import uvicorn
from aioprometheus.asgi.middleware import MetricsMiddleware
from aioprometheus.asgi.starlette import metrics
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simplecrud import user_crud
from simplecrud.lifespan import lifespan
from simplecrud.util.logging_util import setup_json_formatted_logging

setup_json_formatted_logging()

app = FastAPI(title="Simple CRUD", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_crud.router)

app.add_middleware(MetricsMiddleware)
app.add_route("/_health/metrics", metrics)

if __name__ == "__main__":
    debug_log = os.environ.get("DEBUG", False)
    if debug_log:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_config=None)
