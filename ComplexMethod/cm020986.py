async def test_deprecated_timeout_parameter(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_broadcast_config_entry: MockConfigEntry,
    mock_external_calls: None,
    issue_registry: IssueRegistry,
    event: Event | None,
    expected_action_origin: str,
) -> None:
    """Test send message using the deprecated timeout parameter."""

    mock_broadcast_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_broadcast_config_entry.entry_id)
    await hass.async_block_till_done()

    # trigger service call
    context = Context()
    context.origin_event = event
    await hass.services.async_call(
        DOMAIN,
        "send_message",
        {"message": "test message", "timeout": 5},
        blocking=True,
        context=context,
    )

    # check issue is created correctly
    issue = issue_registry.async_get_issue(
        domain=DOMAIN,
        issue_id="deprecated_timeout_parameter",
    )
    assert issue is not None
    assert issue.domain == DOMAIN
    assert issue.translation_key == "deprecated_timeout_parameter"
    assert issue.translation_placeholders == {
        "integration_title": "Telegram Bot",
        "action": "telegram_bot.send_message",
        "action_origin": expected_action_origin,
    }

    # fix the issue via repair flow

    client = await hass_client()
    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": DOMAIN, "issue_id": issue.issue_id},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "form",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "step_id": "confirm",
        "data_schema": [],
        "errors": None,
        "description_placeholders": {
            "integration_title": "Telegram Bot",
            "action": "telegram_bot.send_message",
            "action_origin": expected_action_origin,
        },
        "last_step": None,
        "preview": None,
    }

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "create_entry",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "description": None,
        "description_placeholders": None,
    }

    # verify issue is resolved
    assert not issue_registry.async_get_issue(DOMAIN, "deprecated_timeout_parameter")