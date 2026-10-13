def test_dependency_status_is_ready_only_when_all_dependencies_are_ok():
    dependencies = {"postgres": "ok", "qdrant": "ok"}
    assert "unavailable" not in dependencies.values()


def test_dependency_status_is_not_ready_when_one_dependency_is_unavailable():
    dependencies = {"postgres": "ok", "qdrant": "unavailable"}
    assert "unavailable" in dependencies.values()
