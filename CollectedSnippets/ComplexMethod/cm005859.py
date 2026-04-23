def test_build_provider_update_plan_preserves_operation_encounter_order():
    provider_update = payloads_module.WatsonxDeploymentUpdatePayload.model_validate(
        {
            "tools": {
                "raw_payloads": [
                    {
                        "id": str(UUID("00000000-0000-0000-0000-000000000041")),
                        "name": "snapshot-raw-1",
                        "description": "desc",
                        "data": {"nodes": [], "edges": []},
                        "tags": [],
                        "provider_data": {"project_id": "project-1", "source_ref": "fv-plan-1"},
                    }
                ],
            },
            "connections": {
                "raw_payloads": [
                    {"app_id": "cfg-raw-1", "environment_variables": {"API_KEY": {"source": "raw", "value": "x"}}},
                    {"app_id": "cfg-raw-2", "environment_variables": {"API_KEY": {"source": "raw", "value": "y"}}},
                ],
            },
            "llm": TEST_WXO_LLM,
            "operations": [
                {
                    "op": "bind",
                    "tool": {"tool_id_with_ref": _tool_ref("tool-c")},
                    "app_ids": ["cfg-2", "cfg-1", "cfg-2"],
                },
                {"op": "bind", "tool": {"tool_id_with_ref": _tool_ref("tool-a")}, "app_ids": ["cfg-1"]},
                {"op": "unbind", "tool": _tool_ref("tool-c"), "app_ids": ["cfg-3", "cfg-3"]},
                {"op": "remove_tool", "tool": _tool_ref("tool-b")},
                {"op": "bind", "tool": {"name_of_raw": "snapshot-raw-1"}, "app_ids": ["cfg-raw-2", "cfg-raw-1"]},
            ],
        }
    )
    plan = update_core_module.build_provider_update_plan(
        agent={"id": "dep-1", "tools": ["tool-a", "tool-b"]},
        provider_update=provider_update,
    )

    assert [ref.tool_id for ref in plan.added_existing_tool_refs] == ["tool-c"]
    assert plan.final_existing_tool_ids == ["tool-a", "tool-c"]
    assert plan.existing_app_ids == ["cfg-2", "cfg-1", "cfg-3"]
    assert [item.operation_app_id for item in plan.raw_connections_to_create] == ["cfg-raw-1", "cfg-raw-2"]
    assert [item.provider_app_id for item in plan.raw_connections_to_create] == ["cfg-raw-1", "cfg-raw-2"]
    assert len(plan.raw_tools_to_create) == 1
    assert plan.raw_tools_to_create[0].app_ids == ["cfg-raw-2", "cfg-raw-1"]

    delta = plan.existing_tool_deltas["tool-c"]
    assert delta.bind.to_list() == ["cfg-2", "cfg-1"]
    assert delta.unbind.to_list() == ["cfg-3"]
    assert [ref.tool_id for ref in plan.removed_existing_tool_refs] == ["tool-b"]