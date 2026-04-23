async def test_block_switches(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_websocket_message: WebsocketMessageMock,
    config_entry_setup: MockConfigEntry,
) -> None:
    """Test the update_items function with some clients."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 2

    blocked = hass.states.get("switch.block_client_1_blocked")
    assert blocked is not None
    assert blocked.state == "off"

    unblocked = hass.states.get("switch.block_client_2_blocked")
    assert unblocked is not None
    assert unblocked.state == "on"

    mock_websocket_message(
        message=MessageKey.EVENT, data=EVENT_BLOCKED_CLIENT_UNBLOCKED
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 2
    blocked = hass.states.get("switch.block_client_1_blocked")
    assert blocked is not None
    assert blocked.state == "on"

    mock_websocket_message(message=MessageKey.EVENT, data=EVENT_BLOCKED_CLIENT_BLOCKED)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 2
    blocked = hass.states.get("switch.block_client_1_blocked")
    assert blocked is not None
    assert blocked.state == "off"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/cmd/stamgr",
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.block_client_1_blocked"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[0][2] == {
        "mac": "00:00:00:00:01:01",
        "cmd": "block-sta",
    }

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.block_client_1_blocked"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[1][2] == {
        "mac": "00:00:00:00:01:01",
        "cmd": "unblock-sta",
    }