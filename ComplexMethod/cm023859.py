async def test_availability_in_config(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test entity configuration."""
    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        json={
            "state": "okay",
            "available": True,
            "name": "rest_sensor",
            "icon": "mdi:foo",
            "picture": "foo.jpg",
        },
    )
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "resource": "http://localhost",
                    "sensor": [
                        {
                            "unique_id": "somethingunique",
                            "availability": "{{ value_json.available }}",
                            "value_template": "{{ value_json.state }}",
                            "name": "{{ value_json.name if value_json is defined else 'rest_sensor' }}",
                            "icon": "{{ value_json.icon }}",
                            "picture": "{{ value_json.picture }}",
                        }
                    ],
                }
            ]
        },
    )
    await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.rest_sensor")
    assert state.state == "okay"
    assert state.attributes["friendly_name"] == "rest_sensor"
    assert state.attributes["icon"] == "mdi:foo"
    assert state.attributes["entity_picture"] == "foo.jpg"

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "http://localhost",
        status=HTTPStatus.OK,
        json={
            "state": "okay",
            "available": False,
            "name": "unavailable",
            "icon": "mdi:unavailable",
            "picture": "unavailable.jpg",
        },
    )
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.rest_sensor"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.rest_sensor")
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes["friendly_name"] == "rest_sensor"
    assert "icon" not in state.attributes
    assert "entity_picture" not in state.attributes