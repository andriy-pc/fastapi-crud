from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from simplecrud.database.database_setup import get_session
from simplecrud.health.common_health_checks import (
    MYSQL_HEALTH_TEST_NAME,
    mysql_response_time,
)
from simplecrud.health.health_checker import HealthTest, health_checker

router = APIRouter(tags=["health"])


@router.get("/_health", include_in_schema=False)
async def health(async_session: AsyncSession = Depends(get_session)) -> JSONResponse:
    health_tests = [
        HealthTest(
            name=MYSQL_HEALTH_TEST_NAME,
            method=lambda: mysql_response_time(async_session),
        )
    ]
    return await health_checker(health_tests=health_tests)
