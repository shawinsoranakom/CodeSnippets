async def test_apply_provider_create_plan_binds_raw_tools_with_provider_app_ids(monkeypatch):
    provider_create = payloads_module.WatsonxDeploymentCreatePayload.model_validate(
        {
            "tools": {
                "raw_payloads": [
                    {
                        "id": str(UUID("00000000-0000-0000-0000-000000000081")),
                        "name": "snapshot-raw-1",
                        "description": "desc",
                        "data": {"nodes": [], "edges": []},
                        "tags": [],
                        "provider_data": {"project_id": "project-1", "source_ref": "fv-create-1"},
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
                {"op": "bind", "tool": {"name_of_raw": "snapshot-raw-1"}, "app_ids": ["cfg"]},
            ],
        }
    )
    plan = create_core_module.build_provider_create_plan(
        deployment_name="my deployment",
        provider_create=provider_create,
    )

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

    monkeypatch.setattr(
        create_core_module,
        "create_and_upload_wxo_flow_tools_with_bindings",
        mock_create_and_upload,
    )

    result = await create_core_module.apply_provider_create_plan_with_rollback(
        clients=fake_clients,
        user_id="user-1",
        db=object(),
        deployment_spec=BaseDeploymentData(
            name="my deployment",
            description="desc",
            type=DeploymentType.AGENT,
        ),
        plan=plan,
    )

    assert fake_clients.connections.create_calls == [{"app_id": "cfg"}]
    assert captured["connections"] == {"cfg": "conn-cfg"}
    assert fake_clients.agent.create_calls
    assert fake_clients.agent.create_calls[0]["name"] == "my_deployment"
    assert fake_clients.agent.create_calls[0]["tools"] == ["created-tool-1"]
    assert fake_clients.agent.create_calls[0]["llm"] == TEST_WXO_LLM
    assert result.agent_id == "dep-created"
    assert result.app_ids == ["cfg"]
    assert [(binding.tool_id, binding.app_ids) for binding in result.tool_app_bindings] == [("created-tool-1", ["cfg"])]
    assert [(binding.source_ref, binding.tool_id) for binding in result.tools_with_refs] == [
        ("fv-create-1", "created-tool-1")
    ]