async def test_sensor_removed(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_api: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test sensor removed server side."""

    # Init with reference time
    freezer.move_to(MOCK_REFERENCE_DATE)
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, entry_id="test")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.0_0_0_0_ssl_disk_used").state != STATE_UNAVAILABLE
    assert hass.states.get("sensor.0_0_0_0_memory_use").state != STATE_UNAVAILABLE
    assert hass.states.get("sensor.0_0_0_0_uptime").state != STATE_UNAVAILABLE

    # Remove some sensors from Glances API data
    mock_data = HA_SENSOR_DATA.copy()
    mock_data.pop("fs")
    mock_data.pop("mem")
    mock_data.pop("uptime")
    mock_api.return_value.get_ha_sensor_data = AsyncMock(return_value=mock_data)

    # Server stops providing some sensors, so state should switch to Unavailable
    freezer.move_to(MOCK_REFERENCE_DATE + timedelta(minutes=2))
    freezer.tick(delta=timedelta(seconds=120))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.0_0_0_0_ssl_disk_used").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.0_0_0_0_memory_use").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.0_0_0_0_uptime").state == STATE_UNAVAILABLE