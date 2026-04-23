async def test_create_execution_posts_runs_payload(monkeypatch):
    service = WatsonxOrchestrateDeploymentService(DummySettingsService())
    fake_agent = FakeAgentClient({"id": "dep-1", "tools": []})
    fake_base = FakeBaseClient()
    fake_clients = _with_wxo_wrappers(
        SimpleNamespace(
            _base=fake_base,
            agent=fake_agent,
            tool=FakeToolClient([]),
            connections=FakeConnectionsClient(),
        )
    )

    async def mock_get_provider_clients(*, user_id, db):  # noqa: ARG001
        return fake_clients

    monkeypatch.setattr(service, "_get_provider_clients", mock_get_provider_clients)

    result = await service.create_execution(
        user_id="user-1",
        db=object(),
        payload=ExecutionCreate(
            deployment_id="dep-1",
            provider_data={"input": "hello from test"},
        ),
    )

    assert result.deployment_id == "dep-1"
    assert result.execution_id == "run-1"
    assert result.provider_result["status"] == "accepted"
    assert result.provider_result["execution_id"] == "run-1"
    assert result.provider_result["thread_id"] == "thread-1"
    assert fake_base.post_calls
    path, payload = fake_base.post_calls[0]
    assert path == "/runs"
    assert payload["agent_id"] == "dep-1"
    assert payload["message"] == {"role": "user", "content": "hello from test"}