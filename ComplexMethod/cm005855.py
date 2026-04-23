async def test_update_provider_data_bind_unbind_and_rename_preserves_connection_deltas(monkeypatch):
    service = WatsonxOrchestrateDeploymentService(DummySettingsService())
    fake_agent = FakeAgentClient({"id": "dep-1", "tools": ["tool-1"]})
    fake_tool = FakeToolClient(
        [
            {
                "id": "tool-1",
                "name": "tool-1",
                "display_name": "tool-1",
                "binding": {
                    "langflow": {
                        "connections": {"cfg-keep": "conn-keep", "cfg-remove": "conn-remove"},
                    }
                },
            },
        ]
    )
    fake_clients = SimpleNamespace(
        agent=fake_agent,
        tool=fake_tool,
        connections=FakeConnectionsClient(existing_app_id="cfg-add"),
    )

    async def mock_get_provider_clients(*, user_id, db):  # noqa: ARG001
        return fake_clients

    async def mock_validate_connection(connections_client, *, app_id):  # noqa: ARG001
        connection_id_by_app_id = {
            "cfg-add": "conn-add",
            "cfg-remove": "conn-remove",
        }
        assert app_id in connection_id_by_app_id
        return SimpleNamespace(connection_id=connection_id_by_app_id[app_id])

    monkeypatch.setattr(service, "_get_provider_clients", mock_get_provider_clients)
    monkeypatch.setattr(update_core_module, "validate_connection", mock_validate_connection)

    result = await service.update(
        user_id="user-1",
        deployment_id="dep-1",
        payload=DeploymentUpdate(
            provider_data={
                "tools": {},
                "connections": {},
                "llm": TEST_WXO_LLM,
                "operations": [
                    {"op": "bind", "tool": {"tool_id_with_ref": _tool_ref("tool-1")}, "app_ids": ["cfg-add"]},
                    {"op": "unbind", "tool": _tool_ref("tool-1"), "app_ids": ["cfg-remove"]},
                    {"op": "rename_tool", "tool": _tool_ref("tool-1"), "new_name": "renamed_tool"},
                ],
            }
        ),
        db=object(),
    )

    assert result.provider_result is not None
    assert [tool_id for tool_id, _payload in fake_tool.update_calls] == ["tool-1", "tool-1"]

    _, rename_payload = fake_tool.update_calls[1]
    assert rename_payload["name"] == "renamed_tool"
    assert rename_payload["display_name"] == "renamed_tool"
    assert rename_payload["binding"]["langflow"]["connections"] == {
        "cfg-keep": "conn-keep",
        "cfg-add": "conn-add",
    }

    _, agent_payload = fake_agent.update_calls[0]
    assert agent_payload["tools"] == ["tool-1"]
    assert agent_payload["llm"] == TEST_WXO_LLM