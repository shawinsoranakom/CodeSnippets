async def test_query_param_json_string_preserved(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that JSON strings in query params are preserved and not converted to dicts."""
    # Mock response
    aioclient_mock.get(
        "https://api.example.com/data",
        status=HTTPStatus.OK,
        json={"value": 42},
    )

    # Config with JSON string (quoted) - should remain a string
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {
                    CONF_RESOURCE: "https://api.example.com/data",
                    CONF_METHOD: "GET",
                    CONF_PARAMS: {
                        "filter": '{"type": "sensor", "id": 123}',  # JSON string
                        "normal": "value",
                    },
                    "sensor": [
                        {
                            CONF_NAME: "Test Sensor",
                            CONF_VALUE_TEMPLATE: "{{ value_json.value }}",
                        }
                    ],
                }
            ]
        },
    )
    await hass.async_block_till_done()

    # Check the sensor was created
    assert len(hass.states.async_all(SENSOR_DOMAIN)) == 1
    state = hass.states.get("sensor.test_sensor")
    assert state is not None
    assert state.state == "42"

    # Verify the request was made with the JSON string intact
    assert len(aioclient_mock.mock_calls) == 1
    _method, url, _data, _headers = aioclient_mock.mock_calls[0]
    assert url.query["filter"] == '{"type": "sensor", "id": 123}'
    assert url.query["normal"] == "value"