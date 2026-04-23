async def test_switches(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry_setup: MockConfigEntry,
) -> None:
    """Test the update_items function with some clients."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 3

    # Block and unblock client
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

    # Enable and disable DPI
    aioclient_mock.clear_requests()
    aioclient_mock.put(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/rest/dpiapp/{DPI_APPS[0]['_id']}",
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.unifi_network_block_media_streaming"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[0][2] == {"enabled": False}

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.unifi_network_block_media_streaming"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[1][2] == {"enabled": True}