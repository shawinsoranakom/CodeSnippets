async def test_one_sensor_no_datatype(hass: HomeAssistant, rfxtrx) -> None:
    """Test with 1 sensor."""
    entry_data = create_rfx_test_cfg(devices={"0a52080705020095220269": {}})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    base_id = "sensor.wt260_wt260h_wt440h_wt450_wt450h_05_02"
    base_name = "WT260,WT260H,WT440H,WT450,WT450H 05:02"

    state = hass.states.get(f"{base_id}_temperature")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == f"{base_name} Temperature"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == UnitOfTemperature.CELSIUS

    state = hass.states.get(f"{base_id}_humidity")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == f"{base_name} Humidity"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE

    state = hass.states.get(f"{base_id}_humidity_status")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == f"{base_name} Humidity status"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) is None

    state = hass.states.get(f"{base_id}_signal_strength")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == f"{base_name} Signal strength"
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )

    state = hass.states.get(f"{base_id}_battery")
    assert state
    assert state.state == "unknown"
    assert state.attributes.get("friendly_name") == f"{base_name} Battery"
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE