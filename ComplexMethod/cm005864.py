async def test_get_agent_run_translates_run_id_to_execution_id(monkeypatch):
    """get_agent_run maps WXO id to execution_id and passes through other fields."""
    import asyncio as _asyncio

    from langflow.services.adapters.deployment.watsonx_orchestrate.core.execution import get_agent_run

    wxo_payload = {
        "id": "r-42",
        "status": "completed",
        "agent_id": "agent-1",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:01:00Z",
        "result": {"output": "hello"},
    }

    async def fake_to_thread(fn, *args, **kwargs):  # noqa: ARG001
        return wxo_payload

    monkeypatch.setattr(_asyncio, "to_thread", fake_to_thread)

    fake_client = SimpleNamespace(get_run=lambda _run_id: wxo_payload)
    result = await get_agent_run(fake_client, run_id="r-42")

    assert result["execution_id"] == "r-42"
    assert "run_id" not in result
    assert result["status"] == "completed"
    assert result["agent_id"] == "agent-1"
    assert result["started_at"] == "2026-01-01T00:00:00Z"
    assert result["completed_at"] == "2026-01-01T00:01:00Z"
    assert result["result"] == {"output": "hello"}