async def test_two_weather_sites_running(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    requests_mock: requests_mock.Mocker,
    wavertree_data,
) -> None:
    """Test we handle two different weather sites both running."""

    # all metoffice test data encapsulated in here
    mock_json = json.loads(await async_load_fixture(hass, "metoffice.json", DOMAIN))
    kingslynn_hourly = json.dumps(mock_json["kingslynn_hourly"])
    kingslynn_daily = json.dumps(mock_json["kingslynn_daily"])

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text=kingslynn_hourly,
    )
    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=kingslynn_daily,
    )

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_KINGSLYNN,
    )
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    assert len(device_registry.devices) == 2
    device_kingslynn = device_registry.async_get_device(
        identifiers=DEVICE_KEY_KINGSLYNN
    )
    assert device_kingslynn.name == "Met Office King's Lynn"
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
    assert weather.attributes.get("wind_speed_unit") == "km/h"
    assert weather.attributes.get("wind_bearing") == 176.0
    assert weather.attributes.get("humidity") == 95

    # King's Lynn daily weather platform expected results
    weather = hass.states.get("weather.met_office_king_s_lynn")
    assert weather

    assert weather.state == "rainy"
    assert weather.attributes.get("temperature") == 7.9
    assert weather.attributes.get("wind_speed") == 35.75
    assert weather.attributes.get("wind_speed_unit") == "km/h"
    assert weather.attributes.get("wind_bearing") == 180.0
    assert weather.attributes.get("humidity") == 98