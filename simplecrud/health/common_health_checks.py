import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from simplecrud.health.health_checker import Check, CheckResult, HealthStatus

MYSQL_HEALTH_TEST_NAME = "mysql:responseTime"

log = logging.getLogger(__name__)


async def mysql_response_time(async_session: AsyncSession) -> Check:
    try:
        start_time = time.perf_counter()
        await async_session.execute(text("SELECT 1"))
        end_time = time.perf_counter()
        check_result: CheckResult = CheckResult(
            status=HealthStatus.PASS,
            observedValue=f"{(end_time - start_time) * 1000:0.2f}",
            observedUnit="ms",
        )
    except (SQLAlchemyError, TimeoutError):
        log.warning("Exception occurred during checking if MySQL is reachable")
        check_result = CheckResult(
            status=HealthStatus.FAIL, observedValue="-", observedUnit="ms"
        )

    return Check(name=MYSQL_HEALTH_TEST_NAME, check_results=[check_result])
