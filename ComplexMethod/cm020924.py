async def test_outlet_switches(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_websocket_message: WebsocketMessageMock,
    config_entry_setup: MockConfigEntry,
    device_payload: list[dict[str, Any]],
    entity_id: str,
    outlet_index: int,
    expected_switches: int,
) -> None:
    """Test the outlet entities."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == expected_switches

    # Validate state object
    assert hass.states.get(f"switch.{entity_id}").state == STATE_ON

    # Update state object
    device_1 = deepcopy(device_payload[0])
    device_1["outlet_table"][outlet_index - 1]["relay_state"] = False
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get(f"switch.{entity_id}").state == STATE_OFF

    # Turn off outlet
    device_id = device_payload[0]["device_id"]
    aioclient_mock.clear_requests()
    aioclient_mock.put(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/rest/device/{device_id}",
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: f"switch.{entity_id}"},
        blocking=True,
    )

    expected_off_overrides = deepcopy(device_1["outlet_overrides"])
    expected_off_overrides[outlet_index - 1]["relay_state"] = False

    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[0][2] == {
        "outlet_overrides": expected_off_overrides
    }

    # Turn on outlet
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"switch.{entity_id}"},
        blocking=True,
    )

    expected_on_overrides = deepcopy(device_1["outlet_overrides"])
    expected_on_overrides[outlet_index - 1]["relay_state"] = True
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[1][2] == {
        "outlet_overrides": expected_on_overrides
    }

    # Device gets disabled
    device_1["disabled"] = True
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get(f"switch.{entity_id}").state == STATE_UNAVAILABLE

    # Device gets re-enabled
    device_1["disabled"] = False
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get(f"switch.{entity_id}").state == STATE_OFF