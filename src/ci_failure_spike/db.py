from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CIRun(Base):
    __tablename__ = "ci_runs"
    __table_args__ = (UniqueConstraint("repository", "run_id", "run_attempt"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repository: Mapped[str] = mapped_column(String(300))
    run_id: Mapped[str] = mapped_column(String(100))
    run_attempt: Mapped[int] = mapped_column(Integer)
    commit_sha: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TestFailure(Base):
    __tablename__ = "test_failures"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ci_runs.id", ondelete="CASCADE"), index=True)
    node_id: Mapped[str] = mapped_column(String(1000))
    message: Mapped[str] = mapped_column(Text)
    detail: Mapped[str] = mapped_column(Text)


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True, pool_size=2, max_overflow=1)


async def initialize(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def ready(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def save_run(
    engine: AsyncEngine,
    metadata: dict[str, Any],
    failures: list[Any],
) -> tuple[CIRun, list[TestFailure], bool]:
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        existing = await session.scalar(
            select(CIRun).where(
                CIRun.repository == metadata["repository"],
                CIRun.run_id == metadata["run_id"],
                CIRun.run_attempt == metadata["run_attempt"],
            )
        )
        if existing:
            rows = list((await session.scalars(select(TestFailure).where(TestFailure.run_id == existing.id))).all())
            return existing, rows, False

        run = CIRun(**metadata)
        session.add(run)
        await session.flush()
        rows = [
            TestFailure(run_id=run.id, node_id=item.node_id, message=item.message, detail=item.detail)
            for item in failures
        ]
        session.add_all(rows)
        await session.commit()
        return run, rows, True


async def get_run(engine: AsyncEngine, run_pk: int) -> tuple[CIRun | None, list[TestFailure]]:
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        run = await session.get(CIRun, run_pk)
        if not run:
            return None, []
        rows = list((await session.scalars(select(TestFailure).where(TestFailure.run_id == run_pk))).all())
        return run, rows

