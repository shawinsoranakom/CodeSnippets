async def test_turn_on_off_with_brightness(
    hass: HomeAssistant,
    mock_lunatone_devices: AsyncMock,
    mock_lunatone_info: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the light can be turned on with brightness."""
    device_id = 2
    entity_id = f"light.device_{device_id}"
    expected_brightness = 128
    brightness_percentages = iter([50.0, 0.0, 50.0])

    await setup_integration(hass, mock_config_entry)

    async def fake_update():
        brightness = next(brightness_percentages)
        device = mock_lunatone_devices.data.devices[device_id - 1]
        device.features.switchable.status = brightness > 0
        device.features.dimmable.status = brightness

    mock_lunatone_devices.async_update.side_effect = fake_update

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: expected_brightness},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == expected_brightness

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert not state.attributes["brightness"]

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes["brightness"] == expected_brightness