async def test_watsonx_mapper_create_preserves_env_var_source_in_connection_payloads() -> None:
    """Connections with credentials should preserve source.

    Preserve raw-vs-variable semantics all the way to the adapter payload.
    """
    mapper = WatsonxOrchestrateDeploymentMapper()
    flow_version_id = uuid4()
    flow_id = uuid4()
    project_id = uuid4()
    payload = DeploymentCreateRequest(
        provider_id=uuid4(),
        name="deploy-with-vars",
        description="",
        type="agent",
        provider_data={
            "llm": TEST_WXO_LLM,
            "connections": [
                {
                    "app_id": "app-new",
                    "credentials": [
                        {
                            "key": "RAW_TOKEN",
                            "value": "literal-secret",
                            "source": "raw",
                        },  # pragma: allowlist secret
                        {"key": "VAR_REF", "value": "MY_GLOBAL_VAR", "source": "variable"},
                    ],
                }
            ],
            "add_flows": [
                {
                    "flow_version_id": str(flow_version_id),
                    "app_ids": ["app-new"],
                }
            ],
        },
    )
    row = SimpleNamespace(
        flow_version_id=flow_version_id,
        flow_version_data={"nodes": [], "edges": []},
        flow_id=flow_id,
        flow_name="Flow B",
        flow_description="desc",
        flow_tags=[],
    )

    resolved = await mapper.resolve_deployment_create(
        user_id=uuid4(),
        project_id=project_id,
        db=_FakeDb([row]),
        payload=payload,
    )
    provider_data = resolved.provider_data or {}

    conn_raw_payloads = provider_data["connections"]["raw_payloads"]
    assert conn_raw_payloads is not None
    assert len(conn_raw_payloads) == 1

    env_vars = conn_raw_payloads[0]["environment_variables"]
    assert env_vars["RAW_TOKEN"]["value"] == "literal-secret"  # pragma: allowlist secret
    assert env_vars["RAW_TOKEN"]["source"] == "raw"
    assert env_vars["VAR_REF"]["value"] == "MY_GLOBAL_VAR"
    assert env_vars["VAR_REF"]["source"] == "variable"