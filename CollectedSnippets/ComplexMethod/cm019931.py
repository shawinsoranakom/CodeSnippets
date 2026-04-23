async def test_device_info_gogogate2(
    gogogate2api_mock, hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test device info."""
    closed_door_response = _mocked_gogogate_open_door_response()

    api = MagicMock(GogoGate2Api)
    api.async_info.return_value = closed_door_response
    gogogate2api_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        unique_id="xyz",
        data={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, "xyz")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "mycontroller"
    assert device.model == "gogogate2"
    assert device.sw_version == "222"
    assert device.configuration_url == "http://127.0.0.1"