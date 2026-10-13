import hashlib
import math

VECTOR_SIZE = 64


def deterministic_vector(text: str) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < VECTOR_SIZE:
        digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        values.extend((byte - 127.5) / 127.5 for byte in digest)
        counter += 1
    values = values[:VECTOR_SIZE]
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]

