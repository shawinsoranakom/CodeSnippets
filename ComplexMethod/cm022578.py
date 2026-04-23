async def test_device_management(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that we are adding and removing devices for monitors returned from the API."""
    mock_entry = await setup_uptimerobot_integration(hass)

    devices = dr.async_entries_for_config_entry(device_registry, mock_entry.entry_id)
    assert len(devices) == 1

    assert devices[0].identifiers == {(DOMAIN, "1234")}
    assert devices[0].name == "Test monitor"

    assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
    assert entity.state == STATE_ON
    assert hass.states.get(f"{UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY}_2") is None

    with patch(
        "pyuptimerobot.UptimeRobot.async_get_monitors",
        return_value=mock_uptimerobot_api_response(
            data=[MOCK_UPTIMEROBOT_MONITOR, {**MOCK_UPTIMEROBOT_MONITOR, "id": 12345}]
        ),
    ):
        freezer.tick(COORDINATOR_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(device_registry, mock_entry.entry_id)
    assert len(devices) == 2
    assert devices[0].identifiers == {(DOMAIN, "1234")}
    assert devices[1].identifiers == {(DOMAIN, "12345")}

    assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
    assert entity.state == STATE_ON
    assert (entity2 := hass.states.get(f"{UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY}_2"))
    assert entity2.state == STATE_ON

    with patch(
        "pyuptimerobot.UptimeRobot.async_get_monitors",
        return_value=mock_uptimerobot_api_response(data=[MOCK_UPTIMEROBOT_MONITOR]),
    ):
        freezer.tick(COORDINATOR_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    devices = dr.async_entries_for_config_entry(device_registry, mock_entry.entry_id)
    assert len(devices) == 1
    assert devices[0].identifiers == {(DOMAIN, "1234")}

    assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
    assert entity.state == STATE_ON
    assert hass.states.get(f"{UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY}_2") is None