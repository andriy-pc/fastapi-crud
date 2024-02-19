from http import HTTPStatus
from secrets import token_urlsafe
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from simplecrud.database.database_setup import get_session
from simplecrud.database.model import User
from simplecrud.schema import UpdateUserRequest

router = APIRouter(prefix="/v1/users", tags=["user"])


@router.get(
    path="/{user_id}", response_model_exclude_none=True, status_code=HTTPStatus.OK
)
async def get_user_by_id(
    user_id: str, async_session: Annotated[AsyncSession, Depends(get_session)]
) -> UpdateUserRequest:
    async with async_session.begin():
        user = await async_session.scalar(
            select(User).where(User.external_id == user_id)
        )

    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND.value,
            detail=f"User with id '{user_id}' doesn't exist",
        )

    return UpdateUserRequest(
        id=user.external_id,
        first_name=user.first_name,
        last_name=user.last_name,
        birthday=user.birthday,
    )


@router.post(path="", response_model_exclude_none=True, status_code=HTTPStatus.CREATED)
async def save_user(
    user_dto: UpdateUserRequest,
    async_session: Annotated[AsyncSession, Depends(get_session)],
) -> UpdateUserRequest:
    async with async_session.begin():
        user = User(
            external_id=token_urlsafe(16),
            first_name=user_dto.first_name,
            last_name=user_dto.last_name,
            birthday=user_dto.birthday,
        )
        async_session.add(user)
        return UpdateUserRequest(id=user.external_id)


@router.patch(
    path="/{user_id}",
    response_model_exclude_none=True,
    status_code=HTTPStatus.NO_CONTENT,
)
async def update_by_id(
    user_id: str,
    user_dto: UpdateUserRequest,
    async_session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    async with async_session.begin():
        user_to_update = await async_session.scalar(
            select(User).where(User.external_id == user_id)
        )
        if user_to_update is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND.value,
                detail=f"User with id '{user_id}' doesn't exist",
            )

        user_to_update.first_name = user_dto.first_name or user_to_update.first_name
        user_to_update.last_name = user_dto.last_name or user_to_update.last_name
        user_to_update.birthday = user_dto.birthday or user_to_update.birthday

    return Response(status_code=HTTPStatus.NO_CONTENT.value)


def get_not_none(arg1: Any, arg2: Any) -> Any:
    if arg1 is None:
        return arg2
    return arg1


@router.delete(
    path="/{user_id}",
    response_model_exclude_none=True,
    status_code=HTTPStatus.NO_CONTENT,
)
async def delete_by_id(
    user_id: str, async_session: Annotated[AsyncSession, Depends(get_session)]
) -> Response:
    async with async_session.begin():
        await async_session.execute(delete(User).where(User.external_id == user_id))

    return Response(status_code=HTTPStatus.NO_CONTENT.value)
