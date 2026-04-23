async def test_setup_get(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test setup with valid configuration."""
    aioclient_mock.get("http://localhost", status=HTTPStatus.OK, json={"key": "123"})
    assert await async_setup_component(
        hass,
        SENSOR_DOMAIN,
        {
            SENSOR_DOMAIN: {
                "platform": DOMAIN,
                "resource": "http://localhost",
                "method": "GET",
                "value_template": "{{ value_json.key }}",
                "name": "foo",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "verify_ssl": "true",
                "timeout": 30,
                "authentication": "basic",
                "username": "my username",
                "password": "my password",
                "headers": {"Accept": CONTENT_TYPE_JSON},
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
            }
        },
    )
    await async_setup_component(hass, "homeassistant", {})

    await hass.async_block_till_done()
    assert len(hass.states.async_all(SENSOR_DOMAIN)) == 1

    assert hass.states.get("sensor.foo").state == "123"
    await hass.services.async_call(
        "homeassistant",
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: "sensor.foo"},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("sensor.foo")
    assert state.state == "123"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == UnitOfTemperature.CELSIUS
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.TEMPERATURE
    assert state.attributes[ATTR_STATE_CLASS] is SensorStateClass.MEASUREMENT