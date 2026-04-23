async def test_attributes(hass: HomeAssistant) -> None:
    """Test the binary sensor attributes are correct."""
    await setup_platform(hass, BINARY_SENSOR_DOMAIN)

    state = hass.states.get("binary_sensor.front_door")
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_DEVICE_ID) == "RF:01430030"
    assert not state.attributes.get("battery_low")
    assert not state.attributes.get("no_response")
    assert state.attributes.get("device_type") == "Door Contact"
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "Front Door"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.WINDOW