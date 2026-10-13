from ci_failure_spike.db import normalize_database_url


def test_normalizes_render_postgresql_url_for_asyncpg() -> None:
    assert (
        normalize_database_url("postgresql://user:secret@host:5432/app")
        == "postgresql+asyncpg://user:secret@host:5432/app"
    )


def test_normalizes_legacy_postgres_url_for_asyncpg() -> None:
    assert (
        normalize_database_url("postgres://user:secret@host:5432/app")
        == "postgresql+asyncpg://user:secret@host:5432/app"
    )


def test_preserves_explicit_async_driver_url() -> None:
    url = "postgresql+asyncpg://user:secret@host:5432/app"
    assert normalize_database_url(url) == url
