import pytest

from ci_failure_spike.auth import AuthenticationError, sign, verify


SECRET = "a-secret-that-is-definitely-32-characters"


def test_valid_signature():
    body = b"<testsuite/>"
    signature = sign(SECRET, "1000", body)
    verify(SECRET, "1000", signature, body, 300, now=1100)


@pytest.mark.parametrize(
    ("timestamp", "signature", "message"),
    [(None, None, "missing"), ("bad", "x", "timestamp"), ("1000", "x", "signature")],
)
def test_rejects_invalid_signature(timestamp, signature, message):
    with pytest.raises(AuthenticationError, match=message):
        verify(SECRET, timestamp, signature, b"body", 300, now=1000)


def test_rejects_expired_signature():
    body = b"body"
    with pytest.raises(AuthenticationError, match="expired"):
        verify(SECRET, "1000", sign(SECRET, "1000", body), body, 300, now=1400)

