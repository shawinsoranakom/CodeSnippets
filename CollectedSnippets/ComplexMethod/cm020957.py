async def test_light_color(hass: HomeAssistant, mock_govee_api: AsyncMock) -> None:
    """Test changing color."""
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
        {"entity_id": light.entity_id, ATTR_RGB_COLOR: [100, 255, 50]},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_RGB_COLOR] == (100, 255, 50)
    assert light.attributes[ATTR_COLOR_MODE] == ColorMode.RGB

    mock_govee_api.set_color.assert_awaited_with(
        mock_govee_api.devices[0], rgb=(100, 255, 50), temperature=None
    )

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_COLOR_TEMP_KELVIN: 4400},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_COLOR_TEMP_KELVIN] == 4400
    assert light.attributes[ATTR_COLOR_MODE] == ColorMode.COLOR_TEMP

    mock_govee_api.set_color.assert_awaited_with(
        mock_govee_api.devices[0], rgb=None, temperature=4400
    )