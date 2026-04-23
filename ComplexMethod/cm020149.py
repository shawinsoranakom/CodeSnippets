async def test_mount_failed_repair_flow(
    hass: HomeAssistant,
    supervisor_client: AsyncMock,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test repair flow for mount_failed issue."""
    mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.MOUNT_FAILED,
                context=ContextType.MOUNT,
                reference="backup_share",
                uuid=(issue_uuid := uuid4()),
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_RELOAD,
                    context=ContextType.MOUNT,
                    reference="backup_share",
                    uuid=(sugg_uuid := uuid4()),
                    auto=False,
                ),
                Suggestion(
                    type=SuggestionType.EXECUTE_REMOVE,
                    context=ContextType.MOUNT,
                    reference="backup_share",
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
                    ["mount_execute_reload", "mount_execute_reload"],
                    ["mount_execute_remove", "mount_execute_remove"],
                ],
                "required": False,
                "name": "next_step_id",
            }
        ],
        "menu_options": ["mount_execute_reload", "mount_execute_remove"],
        "description_placeholders": {
            "reference": "backup_share",
            "storage_url": "/config/storage",
        },
    }

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "mount_execute_reload"},
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