async def test_watsonx_mapper_upsert_flow_with_add_remove_and_tool_name_emits_bind_unbind_rename() -> None:
    """upsert_flows with add/remove + tool_name should emit bind, unbind, and rename for existing attachments."""
    mapper = WatsonxOrchestrateDeploymentMapper()
    flow_version_id = uuid4()
    project_id = uuid4()

    flow_row = SimpleNamespace(
        flow_version_id=flow_version_id,
        flow_version_number=1,
        flow_version_data={"nodes": [], "edges": []},
        flow_id=uuid4(),
        flow_name="Flow D",
        flow_description="desc",
        flow_tags=["tag"],
        project_id=project_id,
    )
    attachment_row = SimpleNamespace(
        flow_version_id=flow_version_id,
        provider_snapshot_id="existing-tool-id",
    )

    payload = DeploymentUpdateRequest(
        provider_data={
            "llm": TEST_WXO_LLM,
            "upsert_flows": [
                {
                    "flow_version_id": str(flow_version_id),
                    "add_app_ids": ["app-add-1", "app-add-2"],
                    "remove_app_ids": ["app-remove-1"],
                    "tool_name": "My Mixed Tool",
                }
            ],
        }
    )

    db = _MultiQueryFakeDb(flow_rows=[flow_row], attachment_rows=[attachment_row])

    resolved = await mapper.resolve_deployment_update(
        user_id=uuid4(),
        deployment_db_id=uuid4(),
        db=db,
        payload=payload,
    )
    provider_data = resolved.provider_data or {}

    assert provider_data["operations"][0]["op"] == "bind"
    assert provider_data["operations"][0]["tool"]["tool_id_with_ref"]["tool_id"] == "existing-tool-id"
    assert provider_data["operations"][0]["app_ids"] == ["app-add-1", "app-add-2"]

    assert provider_data["operations"][1]["op"] == "unbind"
    assert provider_data["operations"][1]["tool"]["tool_id"] == "existing-tool-id"
    assert provider_data["operations"][1]["app_ids"] == ["app-remove-1"]

    assert provider_data["operations"][2]["op"] == "rename_tool"
    assert provider_data["operations"][2]["tool"]["tool_id"] == "existing-tool-id"
    assert provider_data["operations"][2]["new_name"] == "My_Mixed_Tool"