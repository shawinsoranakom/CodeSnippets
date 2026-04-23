async def test_one_weather_site_running(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    requests_mock: requests_mock.Mocker,
    wavertree_data,
) -> None:
    """Test the Met Office weather platform."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(device_registry.devices) == 1
    device_wavertree = device_registry.async_get_device(
        identifiers=DEVICE_KEY_WAVERTREE
    )
    assert device_wavertree.name == "Met Office Wavertree"

    # Wavertree daily weather platform expected results
    weather = hass.states.get("weather.met_office_wavertree")
    assert weather

    assert weather.state == "rainy"
    assert weather.attributes.get("temperature") == 9.3
    assert weather.attributes.get("wind_speed") == 28.33
    assert weather.attributes.get("wind_bearing") == 176.0
    assert weather.attributes.get("humidity") == 95