import hashlib
import hmac
import time


class AuthenticationError(ValueError):
    pass


def sign(secret: str, timestamp: str, body: bytes) -> str:
    payload = timestamp.encode("ascii") + b"." + body
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify(
    secret: str,
    timestamp: str | None,
    supplied_signature: str | None,
    body: bytes,
    tolerance_seconds: int,
    now: int | None = None,
) -> None:
    if not timestamp or not supplied_signature:
        raise AuthenticationError("missing signature headers")
    try:
        signed_at = int(timestamp)
    except ValueError as exc:
        raise AuthenticationError("invalid timestamp") from exc
    current = int(time.time()) if now is None else now
    if abs(current - signed_at) > tolerance_seconds:
        raise AuthenticationError("expired timestamp")
    expected = sign(secret, timestamp, body)
    if not hmac.compare_digest(expected, supplied_signature):
        raise AuthenticationError("invalid signature")

