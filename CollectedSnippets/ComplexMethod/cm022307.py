async def test_sensors(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_bridge_v1: Mock
) -> None:
    """Test the update_items function with some sensors."""
    mock_bridge_v1.mock_sensor_responses.append(SENSOR_RESPONSE)
    await setup_platform(
        hass, mock_bridge_v1, [Platform.BINARY_SENSOR, Platform.SENSOR]
    )
    assert len(mock_bridge_v1.mock_requests) == 1
    # 2 "physical" sensors with 3 virtual sensors each
    assert len(hass.states.async_all()) == 7

    presence_sensor_1 = hass.states.get("binary_sensor.living_room_sensor_motion")
    light_level_sensor_1 = hass.states.get("sensor.living_room_sensor_light_level")
    temperature_sensor_1 = hass.states.get("sensor.living_room_sensor_temperature")
    assert presence_sensor_1 is not None
    assert presence_sensor_1.state == "on"
    assert light_level_sensor_1 is not None
    assert light_level_sensor_1.state == "1.0"
    assert light_level_sensor_1.name == "Living room sensor Light level"
    assert temperature_sensor_1 is not None
    assert temperature_sensor_1.state == "17.75"
    assert temperature_sensor_1.name == "Living room sensor Temperature"

    presence_sensor_2 = hass.states.get("binary_sensor.kitchen_sensor_motion")
    light_level_sensor_2 = hass.states.get("sensor.kitchen_sensor_light_level")
    temperature_sensor_2 = hass.states.get("sensor.kitchen_sensor_temperature")
    assert presence_sensor_2 is not None
    assert presence_sensor_2.state == "off"
    assert light_level_sensor_2 is not None
    assert light_level_sensor_2.state == "10.0"
    assert light_level_sensor_2.name == "Kitchen sensor Light level"
    assert temperature_sensor_2 is not None
    assert temperature_sensor_2.state == "18.75"
    assert temperature_sensor_2.name == "Kitchen sensor Temperature"

    battery_remote_1 = hass.states.get("sensor.hue_dimmer_switch_1_battery_level")
    assert battery_remote_1 is not None
    assert battery_remote_1.state == "100"
    assert battery_remote_1.name == "Hue dimmer switch 1 Battery level"

    assert (
        entity_registry.async_get(
            "sensor.hue_dimmer_switch_1_battery_level"
        ).entity_category
        == EntityCategory.DIAGNOSTIC
    )