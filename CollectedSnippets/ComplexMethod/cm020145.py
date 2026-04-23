async def test_supervisor_issue_repair_flow_with_multiple_suggestions(
    hass: HomeAssistant,
    supervisor_client: AsyncMock,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test fix flow for supervisor issue with multiple suggestions."""
    mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.REBOOT_REQUIRED,
                context=ContextType.SYSTEM,
                reference="test",
                uuid=(issue_uuid := uuid4()),
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REBOOT,
                    context=ContextType.SYSTEM,
                    reference="test",
                    uuid=uuid4(),
                    auto=False,
                ),
                Suggestion(
                    type="test_type",
                    context=ContextType.SYSTEM,
                    reference="test",
                    uuid=(sugg_uuid := uuid4()),
                    auto=False,
                ),
            ]
        },
    )

    assert await async_setup_component(hass, "hassio", {})

    repair_issue = issue_registry.async_get_issue(
        domain="hassio", issue_id=issue_uuid.hex
    )
    assert repair_issue

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": "hassio", "issue_id": repair_issue.issue_id},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "menu",
        "flow_id": flow_id,
        "handler": "hassio",
        "step_id": "fix_menu",
        "data_schema": [
            {
                "type": "select",
                "options": [
                    ["system_execute_reboot", "system_execute_reboot"],
                    ["system_test_type", "system_test_type"],
                ],
                "required": False,
                "name": "next_step_id",
            }
        ],
        "menu_options": ["system_execute_reboot", "system_test_type"],
        "description_placeholders": {"reference": "test"},
    }

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}", json={"next_step_id": "system_test_type"}
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "create_entry",
        "flow_id": flow_id,
        "handler": "hassio",
        "description": None,
        "description_placeholders": None,
    }

    assert not issue_registry.async_get_issue(domain="hassio", issue_id=issue_uuid.hex)
    supervisor_client.resolution.apply_suggestion.assert_called_once_with(sugg_uuid)