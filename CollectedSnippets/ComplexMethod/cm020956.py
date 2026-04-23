async def test_light_brightness(hass: HomeAssistant, mock_govee_api: AsyncMock) -> None:
    """Test changing brightness."""
    mock_govee_api.devices = [
        GoveeDevice(
            controller=mock_govee_api,
            ip="192.168.1.100",
            fingerprint="asdawdqwdqwd",
            sku="H615A",
            capabilities=DEFAULT_CAPABILITIES,
        )
    ]

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "off"

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_BRIGHTNESS_PCT: 50},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    mock_govee_api.set_brightness.assert_awaited_with(mock_govee_api.devices[0], 50)
    assert light.attributes[ATTR_BRIGHTNESS] == 127

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_BRIGHTNESS] == 255
    mock_govee_api.set_brightness.assert_awaited_with(mock_govee_api.devices[0], 100)

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_BRIGHTNESS] == 255
    mock_govee_api.set_brightness.assert_awaited_with(mock_govee_api.devices[0], 100)