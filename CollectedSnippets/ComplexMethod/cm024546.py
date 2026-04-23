async def test_sensor_throttling_after_init(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    vehicle_type: str,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test for Renault sensors with a throttling error during setup."""
    mock_fixtures = _get_fixtures(vehicle_type)
    with patch_get_vehicle_data() as patches:
        for key, get_data_mock in patches.items():
            get_data_mock.return_value = mock_fixtures[key]
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    # Initial state
    entity_id = "sensor.reg_zoe_40_battery"
    assert hass.states.get(entity_id).state == "60"
    assert not hass.states.get(entity_id).attributes.get(ATTR_ASSUMED_STATE)
    assert "Renault API throttled: scan skipped" not in caplog.text

    # Test QuotaLimitException state
    caplog.clear()
    for get_data_mock in patches.values():
        get_data_mock.side_effect = QuotaLimitException(
            "err.func.wired.overloaded", "You have reached your quota limit"
        )
    freezer.tick(datetime.timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "60"
    assert hass.states.get(entity_id).attributes.get(ATTR_ASSUMED_STATE)
    assert "Renault API throttled" in caplog.text
    assert "Renault hub currently throttled: scan skipped" in caplog.text

    # Test QuotaLimitException recovery, with new battery level
    caplog.clear()
    for get_data_mock in patches.values():
        get_data_mock.side_effect = None
    patches["battery_status"].return_value.batteryLevel = 55
    freezer.tick(datetime.timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "55"
    assert not hass.states.get(entity_id).attributes.get(ATTR_ASSUMED_STATE)
    assert "Renault API throttled" not in caplog.text
    assert "Renault hub currently throttled: scan skipped" not in caplog.text