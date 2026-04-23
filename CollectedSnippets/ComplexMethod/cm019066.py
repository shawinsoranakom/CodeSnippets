async def test_switch_power_and_energy_sensors_created(
    hass: HomeAssistant,
    vera_component_factory: ComponentFactory,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that switches with metering expose power and energy sensors."""
    vera_switch: pv.VeraSwitch = MagicMock(spec=pv.VeraSwitch)
    vera_switch.device_id = 1
    vera_switch.vera_device_id = vera_switch.device_id
    vera_switch.comm_failure = False
    vera_switch.name = "metered_switch"
    vera_switch.category = 0
    vera_switch.power = 12
    vera_switch.energy = 3

    vera_sensor: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_sensor.device_id = 2
    vera_sensor.vera_device_id = vera_sensor.device_id
    vera_sensor.comm_failure = False
    vera_sensor.name = "dummy_sensor"
    vera_sensor.category = pv.CATEGORY_TEMPERATURE_SENSOR
    vera_sensor.temperature = "20"

    await vera_component_factory.configure_component(
        hass=hass,
        controller_config=new_simple_controller_config(
            devices=(vera_switch, vera_sensor)
        ),
    )
    await hass.async_block_till_done()

    power_entity_id = entity_registry.async_get_entity_id(
        "sensor", "vera", "vera_1111_1_power"
    )
    energy_entity_id = entity_registry.async_get_entity_id(
        "sensor", "vera", "vera_1111_1_energy"
    )

    assert power_entity_id is not None
    assert energy_entity_id is not None

    power_state = hass.states.get(power_entity_id)
    assert power_state is not None
    assert power_state.state == "12"
    assert power_state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "W"

    energy_state = hass.states.get(energy_entity_id)
    assert energy_state is not None
    assert energy_state.state == "3"
    assert energy_state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "kWh"