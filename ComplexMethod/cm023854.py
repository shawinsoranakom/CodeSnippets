async def test_setup_with_endpoint_timeout_with_recovery(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test setup with an endpoint that times out that recovers."""
    await async_setup_component(hass, "homeassistant", {})

    aioclient_mock.get("http://localhost", exc=TimeoutError())
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource": "http://localhost",
                    "method": "GET",
                    "verify_ssl": "false",
                    "timeout": 30,
                    "sensor": [
                        {
                            "unit_of_measurement": UnitOfInformation.MEGABYTES,
                            "name": "sensor1",
                            "value_template": "{{ value_json.sensor1 }}",
                        },
                        {
                            "unit_of_measurement": UnitOfInformation.MEGABYTES,
                            "name": "sensor2",
                            "value_template": "{{ value_json.sensor2 }}",
                        },
                    ],
                    "binary_sensor": [
                        {
                            "name": "binary_sensor1",
                            "value_template": "{{ value_json.binary_sensor1 }}",
                        },
                        {
                            "name": "binary_sensor2",
                            "value_template": "{{ value_json.binary_sensor2 }}",
                        },
                    ],
                }
            ]
        },
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 0

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost",
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )

    # Refresh the coordinator
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()

    # Wait for platform setup retry
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 4

    assert hass.states.get("sensor.sensor1").state == "1"
    assert hass.states.get("sensor.sensor2").state == "2"
    assert hass.states.get("binary_sensor.binary_sensor1").state == "on"
    assert hass.states.get("binary_sensor.binary_sensor2").state == "off"

    # Now the end point flakes out again
    aioclient_mock.clear_requests()
    aioclient_mock.get("http://localhost", exc=TimeoutError())

    # Refresh the coordinator
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()

    assert hass.states.get("sensor.sensor1").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.sensor2").state == STATE_UNAVAILABLE
    assert hass.states.get("binary_sensor.binary_sensor1").state == STATE_UNAVAILABLE
    assert hass.states.get("binary_sensor.binary_sensor2").state == STATE_UNAVAILABLE

    # We request a manual refresh when the
    # endpoint is working again

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost",
        json={
            "sensor1": "1",
            "sensor2": "2",
            "binary_sensor1": "on",
            "binary_sensor2": "off",
        },
    )

    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.sensor1"]},
        blocking=True,
    )
    assert hass.states.get("sensor.sensor1").state == "1"
    assert hass.states.get("sensor.sensor2").state == "2"
    assert hass.states.get("binary_sensor.binary_sensor1").state == "on"
    assert hass.states.get("binary_sensor.binary_sensor2").state == "off"