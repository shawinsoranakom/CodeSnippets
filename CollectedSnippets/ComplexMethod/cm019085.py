async def test_reload(hass: HomeAssistant) -> None:
    """Test hot-reloading derivative YAML sensors."""
    hass.state = ha.CoreState.not_running
    hass.states.async_set("sensor.energy", "0.0")

    config = {
        "sensor": [
            {
                "platform": "derivative",
                "name": "derivative",
                "source": "sensor.energy",
                "unit": "kW",
            },
            {
                "platform": "derivative",
                "name": "derivative_remove",
                "source": "sensor.energy",
                "unit": "kW",
            },
        ]
    }

    assert await async_setup_component(hass, "sensor", config)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 3
    state = hass.states.get("sensor.derivative")
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "kW"
    assert hass.states.get("sensor.derivative_remove")

    yaml_path = get_fixture_path("configuration.yaml", "derivative")
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 3

    # Check that we can change the unit of an existing sensor
    state = hass.states.get("sensor.derivative")
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "W"

    # Check that we can remove a derivative sensor
    assert hass.states.get("sensor.derivative_remove") is None

    # Check that we can add a new derivative sensor
    assert hass.states.get("sensor.derivative_new")