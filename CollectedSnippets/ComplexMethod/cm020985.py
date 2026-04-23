async def test_migrate_chat_id(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_broadcast_config_entry: MockConfigEntry,
    mock_external_calls: None,
    issue_registry: IssueRegistry,
    event: Event | None,
    expected_action_origin: str,
) -> None:
    """Test send message using chat_id as target."""

    mock_broadcast_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_broadcast_config_entry.entry_id)
    await hass.async_block_till_done()

    context = Context()
    context.origin_event = event
    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        {ATTR_TARGET: 654321, ATTR_MESSAGE: "test_message"},
        blocking=True,
        context=context,
        return_response=True,
    )

    assert response == {
        "chats": [
            {
                ATTR_CHAT_ID: 654321,
                ATTR_MESSAGE_ID: 12345,
                ATTR_ENTITY_ID: "notify.mock_title_mock_chat_2",
            }
        ]
    }

    issue_id = (
        f"migrate_chat_ids_in_target_{expected_action_origin}_{SERVICE_SEND_MESSAGE}"
    )
    issue = issue_registry.async_get_issue(
        domain=DOMAIN,
        issue_id=issue_id,
    )
    assert issue is not None
    assert issue.domain == DOMAIN
    assert issue.translation_key == "migrate_chat_ids_in_target"
    assert issue.translation_placeholders == {
        "integration_title": "Telegram Bot",
        "action": "telegram_bot.send_message",
        "action_origin": expected_action_origin,
        "chat_ids": "654321",
        "telegram_bot_entities_url": "/config/entities?domain=telegram_bot",
        "example_old": "```yaml\naction: send_message\ndata:\n  target:  # to be updated\n    - 1234567890\n...\n```",
        "example_new_entity_id": "```yaml\naction: send_message\ndata:\n  entity_id:\n    - notify.telegram_bot_1234567890_1234567890  # replace with your notify entity\n...\n```",
        "example_new_chat_id": "```yaml\naction: send_message\ndata:\n  chat_id:\n    - 1234567890  # replace with your chat_id\n...\n```",
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
            "chat_ids": "654321",
            "telegram_bot_entities_url": "/config/entities?domain=telegram_bot",
            "example_old": "```yaml\naction: send_message\ndata:\n  target:  # to be updated\n    - 1234567890\n...\n```",
            "example_new_entity_id": "```yaml\naction: send_message\ndata:\n  entity_id:\n    - notify.telegram_bot_1234567890_1234567890  # replace with your notify entity\n...\n```",
            "example_new_chat_id": "```yaml\naction: send_message\ndata:\n  chat_id:\n    - 1234567890  # replace with your chat_id\n...\n```",
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