import math

from ci_failure_spike.vector import VECTOR_SIZE, deterministic_vector


def test_vector_is_stable_and_normalized():
    first = deterministic_vector("same failure")
    assert first == deterministic_vector("same failure")
    assert len(first) == VECTOR_SIZE
    assert math.isclose(sum(value * value for value in first), 1.0)

