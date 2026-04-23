async def test_power_plugs(
    hass: HomeAssistant,
    mock_put_request: Callable[[str, str], AiohttpClientMocker],
    light_ws_data: WebsocketDataType,
) -> None:
    """Test that all supported switch entities are created."""
    assert len(hass.states.async_all()) == 4
    assert hass.states.get("switch.on_off_switch").state == STATE_ON
    assert hass.states.get("switch.smart_plug").state == STATE_OFF
    assert hass.states.get("switch.on_off_relay").state == STATE_ON
    assert hass.states.get("switch.unsupported_switch") is None

    await light_ws_data({"state": {"on": False}})
    assert hass.states.get("switch.on_off_switch").state == STATE_OFF

    # Verify service calls

    aioclient_mock = mock_put_request("/lights/0/state")

    # Service turn on power plug

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True}

    # Service turn off power plug

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"on": False}