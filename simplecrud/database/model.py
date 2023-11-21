import datetime

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):  # pylint: disable=too-few-public-methods
    pass


class User(Base):
    __tablename__ = "user"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday: Mapped[datetime.datetime] = mapped_column(nullable=False)
