async def test_thermostat_remote_sensing(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test thermostat remote sensing binary sensors."""
    remote_sensing_attribute = clusters.Thermostat.Attributes.RemoteSensing

    # Test initial state (RemoteSensing = 0, all bits off)
    state = hass.states.get(
        "binary_sensor.mock_thermostat_local_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get(
        "binary_sensor.mock_thermostat_outdoor_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_thermostat_occupancy_remote_sensing")
    assert state
    assert state.state == "off"

    # Set LocalTemperature bit (bit 0)
    set_node_attribute(
        matter_node,
        1,
        remote_sensing_attribute.cluster_id,
        remote_sensing_attribute.attribute_id,
        1,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(
        "binary_sensor.mock_thermostat_local_temperature_remote_sensing"
    )
    assert state
    assert state.state == "on"

    state = hass.states.get(
        "binary_sensor.mock_thermostat_outdoor_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_thermostat_occupancy_remote_sensing")
    assert state
    assert state.state == "off"

    # Set OutdoorTemperature bit (bit 1)
    set_node_attribute(
        matter_node,
        1,
        remote_sensing_attribute.cluster_id,
        remote_sensing_attribute.attribute_id,
        2,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(
        "binary_sensor.mock_thermostat_local_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get(
        "binary_sensor.mock_thermostat_outdoor_temperature_remote_sensing"
    )
    assert state
    assert state.state == "on"

    state = hass.states.get("binary_sensor.mock_thermostat_occupancy_remote_sensing")
    assert state
    assert state.state == "off"

    # Set Occupancy bit (bit 2)
    set_node_attribute(
        matter_node,
        1,
        remote_sensing_attribute.cluster_id,
        remote_sensing_attribute.attribute_id,
        4,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(
        "binary_sensor.mock_thermostat_local_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get(
        "binary_sensor.mock_thermostat_outdoor_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_thermostat_occupancy_remote_sensing")
    assert state
    assert state.state == "on"

    # Set multiple bits (bits 0 and 2 = value 5)
    set_node_attribute(
        matter_node,
        1,
        remote_sensing_attribute.cluster_id,
        remote_sensing_attribute.attribute_id,
        5,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(
        "binary_sensor.mock_thermostat_local_temperature_remote_sensing"
    )
    assert state
    assert state.state == "on"

    state = hass.states.get(
        "binary_sensor.mock_thermostat_outdoor_temperature_remote_sensing"
    )
    assert state
    assert state.state == "off"

    state = hass.states.get("binary_sensor.mock_thermostat_occupancy_remote_sensing")
    assert state
    assert state.state == "on"

    # Set all bits (value 7)
    set_node_attribute(
        matter_node,
        1,
        remote_sensing_attribute.cluster_id,
        remote_sensing_attribute.attribute_id,
        7,
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get(
        "binary_sensor.mock_thermostat_local_temperature_remote_sensing"
    )
    assert state
    assert state.state == "on"

    state = hass.states.get(
        "binary_sensor.mock_thermostat_outdoor_temperature_remote_sensing"
    )
    assert state
    assert state.state == "on"

    state = hass.states.get("binary_sensor.mock_thermostat_occupancy_remote_sensing")
    assert state
    assert state.state == "on"