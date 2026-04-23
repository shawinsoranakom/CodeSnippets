async def test_scene_on(hass: HomeAssistant, mock_govee_api: AsyncMock) -> None:
    """Test turning on scene."""

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

    light = hass.states.get("light.H615A")
    assert light is not None
    assert light.state == "off"

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
    mock_govee_api.turn_on_off.assert_awaited_with(mock_govee_api.devices[0], True)