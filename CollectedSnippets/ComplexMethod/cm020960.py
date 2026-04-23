async def test_scene_restore_temperature(
    hass: HomeAssistant, mock_govee_api: AsyncMock
) -> None:
    """Test restore color temperature."""

    mock_govee_api.devices = [
        GoveeDevice(
            controller=mock_govee_api,
            ip="192.168.1.100",
            fingerprint="asdawdqwdqwd",
            sku="H615A",
            capabilities=SCENE_CAPABILITIES,
        )
    ]

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1

    initial_color = 3456
    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "off"

    # Set initial color
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_COLOR_TEMP_KELVIN: initial_color},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_COLOR_TEMP_KELVIN] == initial_color
    mock_govee_api.turn_on_off.assert_awaited_with(mock_govee_api.devices[0], True)

    # Activate scene
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_EFFECT: "sunrise"},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_EFFECT] == "sunrise"
    mock_govee_api.set_scene.assert_awaited_with(mock_govee_api.devices[0], "sunrise")

    # Deactivate scene
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": light.entity_id, ATTR_EFFECT: "none"},
        blocking=True,
    )
    await hass.async_block_till_done()

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "on"
    assert light.attributes[ATTR_EFFECT] is None
    assert light.attributes[ATTR_COLOR_TEMP_KELVIN] == initial_color