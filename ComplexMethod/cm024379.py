async def test_device_info_startup_off(
    hass: HomeAssistant, client, device_registry: dr.DeviceRegistry
) -> None:
    """Test device info when device is off at startup."""
    client.tv_info.system = {}
    client.tv_state.is_on = False
    entry = await setup_webostv(hass)
    await client.mock_state_update()

    assert hass.states.get(ENTITY_ID).state == STATE_OFF

    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.unique_id)})

    assert device
    assert device.identifiers == {(DOMAIN, entry.unique_id)}
    assert device.manufacturer == "LG"
    assert device.name == TV_NAME
    assert device.sw_version is None
    assert device.model is None