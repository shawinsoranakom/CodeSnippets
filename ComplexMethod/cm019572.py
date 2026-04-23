async def test_air_quality_sensor(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test air quality sensor."""
    # Carbon Dioxide
    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_carbon_dioxide")
    assert state
    assert state.state == "678.0"

    set_node_attribute(matter_node, 1, 1037, 0, 789)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_carbon_dioxide")
    assert state
    assert state.state == "789.0"

    # Nitrogen Dioxide
    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_nitrogen_dioxide")
    assert state
    assert state.state == "0.0"
    assert state.attributes["device_class"] == "nitrogen_dioxide"

    set_node_attribute(matter_node, 1, 1043, 0, 12.5)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_nitrogen_dioxide")
    assert state
    assert state.state == "12.5"

    # PM1
    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_pm1")
    assert state
    assert state.state == "3.0"

    set_node_attribute(matter_node, 1, 1068, 0, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_pm1")
    assert state
    assert state.state == "50.0"

    # PM2.5
    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_pm2_5")
    assert state
    assert state.state == "3.0"

    set_node_attribute(matter_node, 1, 1066, 0, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_pm2_5")
    assert state
    assert state.state == "50.0"

    # PM10
    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_pm10")
    assert state
    assert state.state == "3.0"

    set_node_attribute(matter_node, 1, 1069, 0, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_pm10")
    assert state
    assert state.state == "50.0"

    # Radon
    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_radon_concentration")
    assert state
    assert state.state == "60.0"

    set_node_attribute(matter_node, 1, 1071, 0, 50)
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.lightfi_aq1_air_quality_sensor_radon_concentration")
    assert state
    assert state.state == "50.0"