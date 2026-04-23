async def test_sensor(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_station_details: Station,
    mock_station_measurement: StationMeasurements,
    expected_states: dict,
) -> None:
    """Tests sensor entity."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_entry_data,
        unique_id=mock_config_entry_data[CONF_STATION],
    )
    entry.add_to_hass(hass)
    with patch("homeassistant.components.pegel_online.PegelOnline") as pegelonline:
        pegelonline.return_value = PegelOnlineMock(
            station_details=mock_station_details,
            station_measurements=mock_station_measurement,
        )
        assert await hass.config_entries.async_setup(entry.entry_id)

    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == len(expected_states)

    for state_name, state_data in expected_states.items():
        state = hass.states.get(state_name)
        assert state.name == state_data[0]
        assert state.state == state_data[1]
        assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == state_data[2]
        if mock_station_details.latitude is not None:
            assert state.attributes[ATTR_LATITUDE] == mock_station_details.latitude
            assert state.attributes[ATTR_LONGITUDE] == mock_station_details.longitude