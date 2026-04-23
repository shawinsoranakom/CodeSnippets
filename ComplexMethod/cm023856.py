async def test_setup_timestamp(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test setup with valid configuration."""
    aioclient_mock.get(
        "http://localhost", status=HTTPStatus.OK, json={"key": "2021-11-11 11:39Z"}
    )
    assert await async_setup_component(
        hass,
        SENSOR_DOMAIN,
        {
            SENSOR_DOMAIN: {
                "platform": DOMAIN,
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.key }}",
                "device_class": SensorDeviceClass.TIMESTAMP,
            }
        },
    )
    await async_setup_component(hass, "homeassistant", {})

    await hass.async_block_till_done()
    assert len(hass.states.async_all(SENSOR_DOMAIN)) == 1

    state = hass.states.get("sensor.rest_sensor")
    assert state.state == "2021-11-11T11:39:00+00:00"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP
    assert "sensor.rest_sensor rendered invalid timestamp" not in caplog.text
    assert "sensor.rest_sensor rendered timestamp without timezone" not in caplog.text

    # Bad response: Not a timestamp
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost", status=HTTPStatus.OK, json={"key": "invalid time stamp"}
    )
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.rest_sensor"]},
        blocking=True,
    )
    state = hass.states.get("sensor.rest_sensor")
    assert state.state == "unknown"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP
    assert "sensor.rest_sensor rendered invalid timestamp" in caplog.text

    # Bad response: No timezone
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost", status=HTTPStatus.OK, json={"key": "2021-10-11 11:39"}
    )
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.rest_sensor"]},
        blocking=True,
    )
    state = hass.states.get("sensor.rest_sensor")
    assert state.state == "unknown"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TIMESTAMP
    assert "sensor.rest_sensor rendered timestamp without timezone" in caplog.text