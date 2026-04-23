async def test_trend_energy_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_sense: MagicMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test the Sense power sensors."""
    mock_sense.get_stat.side_effect = lambda sensor_type, variant: {
        (Scale.DAY, "usage"): 100,
        (Scale.DAY, "production"): 200,
        (Scale.DAY, "from_grid"): 300,
        (Scale.DAY, "to_grid"): 400,
        (Scale.DAY, "net_production"): 500,
        (Scale.DAY, "production_pct"): 600,
        (Scale.DAY, "solar_powered"): 700,
    }.get((sensor_type, variant), 0)

    await setup_platform(hass, config_entry, SENSOR_DOMAIN)

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_energy")
    assert state.state == "100"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_production")
    assert state.state == "200"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_from_grid")
    assert state.state == "300"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_to_grid")
    assert state.state == "400"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_net_production")
    assert state.state == "500"

    mock_sense.get_stat.side_effect = lambda sensor_type, variant: {
        (Scale.DAY, "usage"): 1000,
        (Scale.DAY, "production"): 2000,
        (Scale.DAY, "from_grid"): 3000,
        (Scale.DAY, "to_grid"): 4000,
        (Scale.DAY, "net_production"): 5000,
        (Scale.DAY, "production_pct"): 6000,
        (Scale.DAY, "solar_powered"): 7000,
    }.get((sensor_type, variant), 0)
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=600))
    await hass.async_block_till_done()

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_energy")
    assert state.state == "1000"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_production")
    assert state.state == "2000"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_from_grid")
    assert state.state == "3000"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_to_grid")
    assert state.state == "4000"

    state = hass.states.get(f"sensor.sense_{MONITOR_ID}_daily_net_production")
    assert state.state == "5000"