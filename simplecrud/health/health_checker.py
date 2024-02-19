import asyncio
import logging
from asyncio import CancelledError
from enum import Enum
from http import HTTPStatus
from typing import Any, Callable, Coroutine, Sequence, Set

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import JSONResponse


class HealthStatus(Enum):
    PASS = "pass"
    FAIL = "fail"


class CheckResult(BaseModel):
    componentId: str | None = None
    observedValue: str
    observedUnit: str
    status: HealthStatus


class Check(BaseModel):
    name: str
    check_results: list[CheckResult]


class HealthTest(BaseModel):
    name: str
    method: Callable[..., Coroutine[Any, Any, Check | None]]


_health_checker_tasks: Set[asyncio.Task[Check | None]] = set()

log = logging.getLogger(__name__)


async def health_checker(health_tests: Sequence[HealthTest]) -> JSONResponse:
    for health_test in health_tests:
        task = asyncio.create_task(health_test.method(), name=health_test.name)
        task.add_done_callback(
            lambda health_task: _health_checker_tasks.discard(health_task)
        )
        _health_checker_tasks.add(task)

    health_results = []
    try:
        health_results = await asyncio.gather(*_health_checker_tasks)
    except CancelledError:
        log.debug("Health check tests running too long")

    results: list[Check] = [res for res in health_results if res is not None]
    checks: dict[str, list[CheckResult]] = {}

    for check in results:
        checks[check.name] = check.check_results

    health_status = calculate_application_health_status(results)
    output = {
        "status": health_status,
        "checks": checks,
    }
    return JSONResponse(
        jsonable_encoder(output, exclude_none=True),
        status_code=http_code_based_on_status(output),
        headers={"content-type": "application/health+json"},
    )


def calculate_application_health_status(checks: list[Check]) -> HealthStatus:
    for check in checks:
        for check_result in check.check_results:
            if check_result.status == HealthStatus.FAIL:
                return HealthStatus.FAIL

    return HealthStatus.PASS


def http_code_based_on_status(health_response: dict[str, Any]) -> int:
    if health_response["status"] == HealthStatus.PASS:
        return HTTPStatus.OK.value
    else:
        return HTTPStatus.SERVICE_UNAVAILABLE.value
