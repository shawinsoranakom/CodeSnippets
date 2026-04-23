async def test_supervisor_issue_detached_addon_removed(
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
                type=IssueType.DETACHED_ADDON_REMOVED,
                context=ContextType.ADDON,
                reference="test",
                uuid=(issue_uuid := uuid4()),
            ),
        ],
        suggestions_by_issue={
            issue_uuid: [
                Suggestion(
                    type=SuggestionType.EXECUTE_REMOVE,
                    context=ContextType.ADDON,
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
        "type": "form",
        "flow_id": flow_id,
        "handler": "hassio",
        "step_id": "addon_execute_remove",
        "data_schema": [],
        "errors": None,
        "description_placeholders": {
            "reference": "test",
            "addon": "test",
            "help_url": "https://www.home-assistant.io/help/",
            "community_url": "https://community.home-assistant.io/",
        },
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