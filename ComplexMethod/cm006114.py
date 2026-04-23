async def test_watsonx_mapper_tool_name_rename_compatible_with_all_update_operation_families() -> None:
    """tool_name/rename should coexist with flow removals, tool upserts/removals, and spec updates."""
    mapper = WatsonxOrchestrateDeploymentMapper()
    flow_version_id_upsert = uuid4()
    flow_version_id_remove = uuid4()
    project_id = uuid4()

    flow_row = SimpleNamespace(
        flow_version_id=flow_version_id_upsert,
        flow_version_number=1,
        flow_version_data={"nodes": [], "edges": []},
        flow_id=uuid4(),
        flow_name="Flow E",
        flow_description="desc",
        flow_tags=["tag"],
        project_id=project_id,
    )
    attachment_rows = [
        SimpleNamespace(
            flow_version_id=flow_version_id_upsert,
            provider_snapshot_id="existing-tool-upsert",
        ),
        SimpleNamespace(
            flow_version_id=flow_version_id_remove,
            provider_snapshot_id="existing-tool-remove",
        ),
    ]

    payload = DeploymentUpdateRequest(
        name="updated-name",
        description="updated-description",
        provider_data={
            "llm": TEST_WXO_LLM,
            "connections": [],
            "upsert_flows": [
                {
                    "flow_version_id": str(flow_version_id_upsert),
                    "add_app_ids": ["app-add"],
                    "remove_app_ids": ["app-remove"],
                    "tool_name": "My Combined Tool",
                }
            ],
            "remove_flows": [str(flow_version_id_remove)],
            "upsert_tools": [
                {
                    "tool_id": "external-tool-upsert",
                    "add_app_ids": ["external-app-add"],
                    "remove_app_ids": [],
                }
            ],
            "remove_tools": ["external-tool-remove"],
        },
    )

    db = _MultiQueryFakeDb(flow_rows=[flow_row], attachment_rows=attachment_rows)

    resolved = await mapper.resolve_deployment_update(
        user_id=uuid4(),
        deployment_db_id=uuid4(),
        db=db,
        payload=payload,
    )
    provider_data = resolved.provider_data or {}

    assert resolved.spec is not None
    assert resolved.spec.name == "updated-name"
    assert resolved.spec.description == "updated-description"
    assert provider_data["llm"] == TEST_WXO_LLM
    assert provider_data["tools"]["raw_payloads"] is None

    ops = provider_data["operations"]
    assert [op["op"] for op in ops] == ["bind", "unbind", "rename_tool", "remove_tool", "bind", "remove_tool"]

    assert ops[0]["tool"]["tool_id_with_ref"]["tool_id"] == "existing-tool-upsert"
    assert ops[0]["app_ids"] == ["app-add"]

    assert ops[1]["tool"]["tool_id"] == "existing-tool-upsert"
    assert ops[1]["app_ids"] == ["app-remove"]

    assert ops[2]["tool"]["tool_id"] == "existing-tool-upsert"
    assert ops[2]["new_name"] == "My_Combined_Tool"

    assert ops[3]["tool"]["tool_id"] == "existing-tool-remove"

    assert ops[4]["tool"]["tool_id_with_ref"]["tool_id"] == "external-tool-upsert"
    assert ops[4]["app_ids"] == ["external-app-add"]

    assert ops[5]["tool"]["tool_id"] == "external-tool-remove"