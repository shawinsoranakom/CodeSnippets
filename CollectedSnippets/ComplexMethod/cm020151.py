async def test_supervisor_issue_repair_flow_multiple_data_disks(
    hass: HomeAssistant,
    supervisor_client: AsyncMock,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test fix flow for multiple data disks supervisor issue."""
    mock_resolution_info(
        supervisor_client,
        issues=[
            Issue(
                type=IssueType.MULTIPLE_DATA_DISKS,
                context=ContextType.SYSTEM,
                reference="/dev/sda1",
                uuid=(issue_uuid := uuid4()),
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.RENAME_DATA_DISK,
                    context=ContextType.SYSTEM,
                    reference="/dev/sda1",
                    uuid=uuid4(),
                    auto=False,
                ),
                Suggestion(
                    type=SuggestionType.ADOPT_DATA_DISK,
                    context=ContextType.SYSTEM,
                    reference="/dev/sda1",
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
                    ["system_rename_data_disk", "system_rename_data_disk"],
                    ["system_adopt_data_disk", "system_adopt_data_disk"],
                ],
                "required": False,
                "name": "next_step_id",
            }
        ],
        "menu_options": ["system_rename_data_disk", "system_adopt_data_disk"],
        "description_placeholders": {"reference": "/dev/sda1"},
    }

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "system_adopt_data_disk"},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "form",
        "flow_id": flow_id,
        "handler": "hassio",
        "step_id": "system_adopt_data_disk",
        "data_schema": [],
        "errors": None,
        "description_placeholders": {"reference": "/dev/sda1"},
        "last_step": True,
        "preview": None,
    }

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

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