async def test_several_sensors(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 3 sensors."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0a52080705020095220269": {},
            "0a520802060100ff0e0269": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("sensor.wt260_wt260h_wt440h_wt450_wt450h_05_02_temperature")
    assert state
    assert state.state == "unknown"
    assert (
        state.attributes.get("friendly_name")
        == "WT260,WT260H,WT440H,WT450,WT450H 05:02 Temperature"
    )
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    state = hass.states.get("sensor.wt260_wt260h_wt440h_wt450_wt450h_06_01_temperature")
    assert state
    assert state.state == "unknown"
    assert (
        state.attributes.get("friendly_name")
        == "WT260,WT260H,WT440H,WT450,WT450H 06:01 Temperature"
    )
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    state = hass.states.get("sensor.wt260_wt260h_wt440h_wt450_wt450h_06_01_humidity")
    assert state
    assert state.state == "unknown"
    assert (
        state.attributes.get("friendly_name")
        == "WT260,WT260H,WT440H,WT450,WT450H 06:01 Humidity"
    )
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE