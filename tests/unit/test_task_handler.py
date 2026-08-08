from src.handlers.task_handlers import task_handler


def test_handler_uses_task_id_env_var(monkeypatch):
    monkeypatch.setenv("TASK_ID", "nightly-cleanup")
    response = task_handler({}, None)

    assert response["ok"] is True
    assert response["task_id"] == "nightly-cleanup"
    assert response["scheduler"] == "eventbridge-rule"
    assert response["data"] == "Nightly cleanup done (scope=all)"


def test_handler_passes_event_input_as_params(monkeypatch):
    monkeypatch.setenv("TASK_ID", "sync-things")
    response = task_handler({"region": "eu-west-1"}, None)

    assert response["ok"] is True
    assert response["data"] == "Sync completed (region=eu-west-1)"


def test_event_task_id_overrides_env(monkeypatch):
    monkeypatch.setenv("TASK_ID", "sync-things")
    response = task_handler({"task_id": "nightly-cleanup", "scope": "logs"}, None)

    assert response["task_id"] == "nightly-cleanup"
    assert response["data"] == "Nightly cleanup done (scope=logs)"


def test_missing_task_id_returns_error(monkeypatch):
    monkeypatch.delenv("TASK_ID", raising=False)
    response = task_handler({}, None)

    assert response["ok"] is False
    assert "TASK_ID" in response["error"]


def test_unknown_task_returns_error(monkeypatch):
    monkeypatch.setenv("TASK_ID", "does-not-exist")
    response = task_handler({}, None)

    assert response["ok"] is False
    assert response["task_id"] == "does-not-exist"


def test_none_event_is_tolerated(monkeypatch):
    monkeypatch.setenv("TASK_ID", "nightly-cleanup")
    assert task_handler(None, None)["ok"] is True
