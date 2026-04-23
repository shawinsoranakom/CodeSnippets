async def test_binary_sensors(
    hass: HomeAssistant, mock_bridge_v2: Mock, v2_resources_test_data: JsonArrayType
) -> None:
    """Test if all v2 binary_sensors get created with correct features."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.BINARY_SENSOR)
    # there shouldn't have been any requests at this point
    assert len(mock_bridge_v2.mock_requests) == 0
    # 7 binary_sensors should be created from test data

    # test motion sensor
    sensor = hass.states.get("binary_sensor.hue_motion_sensor_motion")
    assert sensor is not None
    assert sensor.state == "off"
    assert sensor.name == "Hue motion sensor Motion"
    assert sensor.attributes["device_class"] == "motion"

    # test entertainment room active sensor
    sensor = hass.states.get("binary_sensor.philips_hue_entertainmentroom_1")
    assert sensor is not None
    assert sensor.state == "off"
    assert sensor.name == "Philips hue Entertainmentroom 1"
    assert sensor.attributes["device_class"] == "running"

    # test contact sensor
    sensor = hass.states.get("binary_sensor.test_contact_sensor_opening")
    assert sensor is not None
    assert sensor.state == "off"
    assert sensor.name == "Test contact sensor Opening"
    assert sensor.attributes["device_class"] == "opening"
    # test contact sensor disabled == state unknown
    mock_bridge_v2.api.emit_event(
        "update",
        {
            "enabled": False,
            "id": "18802b4a-b2f6-45dc-8813-99cde47f3a4a",
            "type": "contact",
        },
    )
    await hass.async_block_till_done()
    sensor = hass.states.get("binary_sensor.test_contact_sensor_opening")
    assert sensor.state == "unknown"

    # test tamper sensor
    sensor = hass.states.get("binary_sensor.test_contact_sensor_tamper")
    assert sensor is not None
    assert sensor.state == "off"
    assert sensor.name == "Test contact sensor Tamper"
    assert sensor.attributes["device_class"] == "tamper"
    # test tamper sensor when no tamper reports exist
    mock_bridge_v2.api.emit_event(
        "update",
        {
            "id": "d7fcfab0-69e1-4afb-99df-6ed505211db4",
            "tamper_reports": [],
            "type": "tamper",
        },
    )
    await hass.async_block_till_done()
    sensor = hass.states.get("binary_sensor.test_contact_sensor_tamper")
    assert sensor.state == "off"

    # test camera_motion sensor
    sensor = hass.states.get("binary_sensor.test_camera_motion")
    assert sensor is not None
    assert sensor.state == "on"
    assert sensor.name == "Test Camera Motion"
    assert sensor.attributes["device_class"] == "motion"

    # test grouped motion sensor
    sensor = hass.states.get("binary_sensor.sensor_group_motion")
    assert sensor is not None
    assert sensor.state == "off"
    assert sensor.name == "Sensor group Motion"
    assert sensor.attributes["device_class"] == "motion"

    # test motion aware sensor
    sensor = hass.states.get("binary_sensor.test_room_motion_aware_sensor_1")
    assert sensor is not None
    assert sensor.state == "off"
    assert sensor.name == "Test Room Motion Aware Sensor 1"
    assert sensor.attributes["device_class"] == "motion"