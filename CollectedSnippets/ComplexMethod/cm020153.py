async def test_supervisor_issue_addon_boot_fail(
    hass: HomeAssistant,
    supervisor_client: AsyncMock,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test fix flow for supervisor issue."""
    mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type="boot_fail",
                context=ContextType.ADDON,
                reference="test",
                uuid=(issue_uuid := uuid4()),
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type="execute_start",
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=(sugg_uuid := uuid4()),
                    auto=False,
                ),
                Suggestion(
                    type="disable_boot",
                    context=ContextType.ADDON,
                    reference="test",
                    uuid=uuid4(),
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
                    ["addon_execute_start", "addon_execute_start"],
                    ["addon_disable_boot", "addon_disable_boot"],
                ],
                "required": False,
                "name": "next_step_id",
            }
        ],
        "menu_options": ["addon_execute_start", "addon_disable_boot"],
        "description_placeholders": {
            "reference": "test",
            "addon": "test",
        },
    }

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "addon_execute_start"},
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