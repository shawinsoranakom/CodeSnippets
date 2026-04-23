async def test_price_sensor_state_unit_and_attributes(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    tibber_mock: MagicMock,
    setup_credentials: None,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test price sensor state and attributes."""
    home = _create_home(current_price=1.25)
    tibber_mock.get_homes.return_value = [home]

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, home.home_id)
    assert entity_id is not None

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 1.25
    assert state.attributes["unit_of_measurement"] == "NOK/kWh"
    assert state.attributes["app_nickname"] == "Home"
    assert state.attributes["grid_company"] == "GridCo"
    assert state.attributes["estimated_annual_consumption"] == 12000
    assert state.attributes["intraday_price_ranking"] == 0.4
    assert state.attributes["max_price"] == 1.8
    assert state.attributes["avg_price"] == 1.2
    assert state.attributes["min_price"] == 0.8
    assert state.attributes["off_peak_1"] == 0.9
    assert state.attributes["peak"] == 1.7
    assert state.attributes["off_peak_2"] == 1.0

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 1.25
    assert state.attributes["unit_of_measurement"] == "NOK/kWh"
    assert state.attributes["app_nickname"] == "Home"
    assert state.attributes["grid_company"] == "GridCo"
    assert state.attributes["estimated_annual_consumption"] == 12000
    assert state.attributes["intraday_price_ranking"] == 0.4
    assert state.attributes["max_price"] == 1.8
    assert state.attributes["avg_price"] == 1.2
    assert state.attributes["min_price"] == 0.8
    assert state.attributes["off_peak_1"] == 0.9
    assert state.attributes["peak"] == 1.7
    assert state.attributes["off_peak_2"] == 1.0