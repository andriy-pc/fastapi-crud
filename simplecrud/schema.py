import datetime

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core.core_schema import ValidationInfo


def to_camel_case(snake_case: str) -> str:
    words = snake_case.split("_")
    return words[0] + "".join([word.capitalize() for word in words[1:]])


class UpdateUserRequest(BaseModel):
    id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    birthday: datetime.datetime | None = None

    @field_validator("id", "first_name", "last_name")
    @classmethod
    def check_not_empty_not_blank(cls, field: str, info: ValidationInfo) -> str:
        if field is None or not field.strip():
            raise ValueError(f"{info.field_name} can not be empty or blank")
        return field

    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True)
