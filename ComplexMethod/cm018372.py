async def test_two_sensor_sites_running(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    requests_mock: requests_mock.Mocker,
) -> None:
    """Test we handle two sets of sensors running for two different sites."""

    # all metoffice test data encapsulated in here
    mock_json = json.loads(await async_load_fixture(hass, "metoffice.json", DOMAIN))
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])
    kingslynn_hourly = json.dumps(mock_json["kingslynn_hourly"])
    kingslynn_daily = json.dumps(mock_json["kingslynn_daily"])

    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text=wavertree_hourly,
    )
    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

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

    running_sensor_ids = hass.states.async_entity_ids("sensor")
    assert len(running_sensor_ids) > 0
    for running_id in running_sensor_ids:
        sensor = hass.states.get(running_id)
        if "wavertree" in running_id:
            sensor_id = re.search("met_office_wavertree_(.+?)$", running_id).group(1)
            sensor_value = WAVERTREE_SENSOR_RESULTS[sensor_id]
            assert (
                get_sensor_display_state(hass, entity_registry, running_id)
                == sensor_value
            )
            assert (
                sensor.attributes.get("last_update").isoformat() == TEST_DATETIME_STRING
            )
            assert sensor.attributes.get("attribution") == ATTRIBUTION

        else:
            sensor_id = re.search("met_office_king_s_lynn_(.+?)$", running_id).group(1)
            sensor_value = KINGSLYNN_SENSOR_RESULTS[sensor_id]
            assert (
                get_sensor_display_state(hass, entity_registry, running_id)
                == sensor_value
            )
            assert (
                sensor.attributes.get("last_update").isoformat() == TEST_DATETIME_STRING
            )
            assert sensor.attributes.get("attribution") == ATTRIBUTION