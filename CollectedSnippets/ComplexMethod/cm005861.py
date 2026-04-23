async def test_create_provider_data_prefixes_tool_and_deployment_names_but_not_connection_app_ids(monkeypatch):
    service = WatsonxOrchestrateDeploymentService(DummySettingsService())
    fake_clients = FakeWXOClients(
        agent=FakeAgentClient({"id": "dep-1", "tools": []}),
        tool=FakeToolClient([]),
        connections=FakeConnectionsClient(),
    )
    captured: dict[str, Any] = {}

    async def mock_create_and_upload(*, clients, tool_bindings):
        _ = clients
        first_binding = tool_bindings[0]
        captured["connections"] = first_binding.connections
        return ["created-tool-1"]

    _attach_provider_clients(service, fake_clients)
    monkeypatch.setattr(
        create_core_module,
        "create_and_upload_wxo_flow_tools_with_bindings",
        mock_create_and_upload,
    )

    result = await service.create(
        user_id="user-1",
        payload=DeploymentCreate(
            spec=BaseDeploymentData(
                name="my deployment",
                description="desc",
                type=DeploymentType.AGENT,
            ),
            provider_data={
                "tools": {
                    "raw_payloads": [
                        {
                            "id": str(UUID("00000000-0000-0000-0000-000000000091")),
                            "name": "snapshot-new-1",
                            "description": "desc",
                            "data": {"nodes": [], "edges": []},
                            "tags": [],
                            "provider_data": {"project_id": "project-1", "source_ref": "fv-create-service-1"},
                        }
                    ]
                },
                "connections": {
                    "raw_payloads": [
                        {"app_id": "cfg", "environment_variables": {"API_KEY": {"source": "raw", "value": "x"}}}
                    ]
                },
                "llm": TEST_WXO_LLM,
                "operations": [
                    {"op": "bind", "tool": {"name_of_raw": "snapshot-new-1"}, "app_ids": ["cfg"]},
                ],
            },
        ),
        db=object(),
    )

    assert fake_clients.connections.create_calls == [{"app_id": "cfg"}]
    assert captured["connections"] == {"cfg": "conn-cfg"}
    assert fake_clients.agent.create_calls
    assert fake_clients.agent.create_calls[0]["name"] == "my_deployment"
    assert fake_clients.agent.create_calls[0]["display_name"] == "my deployment"
    assert fake_clients.agent.create_calls[0]["description"] == "desc"
    assert fake_clients.agent.create_calls[0]["tools"] == ["created-tool-1"]
    assert fake_clients.agent.create_calls[0]["llm"] == TEST_WXO_LLM
    assert result.config_id is None
    assert result.snapshot_ids == []
    assert result.provider_result is not None
    provider_result = (
        result.provider_result.model_dump() if hasattr(result.provider_result, "model_dump") else result.provider_result
    )
    assert provider_result["app_ids"] == ["cfg"]
    assert provider_result["tool_app_bindings"] == [{"tool_id": "created-tool-1", "app_ids": ["cfg"]}]
    assert provider_result["tools_with_refs"] == [{"source_ref": "fv-create-service-1", "tool_id": "created-tool-1"}]