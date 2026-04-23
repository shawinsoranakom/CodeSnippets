async def test_query_climate_request_f(
    hass_fixture, assistant_client, auth_header
) -> None:
    """Test a query request."""
    # Mock demo devices as fahrenheit to see if we convert to celsius
    hass_fixture.config.units = US_CUSTOMARY_SYSTEM
    for entity_id in ("climate.hvac", "climate.heatpump", "climate.ecobee"):
        state = hass_fixture.states.get(entity_id)
        attr = dict(state.attributes)
        hass_fixture.states.async_set(entity_id, state.state, attr)

    reqid = "5711642932632160984"
    data = {
        "requestId": reqid,
        "inputs": [
            {
                "intent": "action.devices.QUERY",
                "payload": {
                    "devices": [
                        {"id": "climate.hvac"},
                        {"id": "climate.heatpump"},
                        {"id": "climate.ecobee"},
                    ]
                },
            }
        ],
    }
    result = await assistant_client.post(
        ga.const.GOOGLE_ASSISTANT_API_ENDPOINT,
        data=json.dumps(data),
        headers=auth_header,
    )
    assert result.status == HTTPStatus.OK
    body = await result.json()
    assert body.get("requestId") == reqid
    devices = body["payload"]["devices"]
    assert len(devices) == 3
    assert devices["climate.heatpump"] == {
        "online": True,
        "on": True,
        "thermostatTemperatureSetpoint": -6.7,
        "thermostatTemperatureAmbient": -3.9,
        "thermostatMode": "heat",
    }
    assert devices["climate.ecobee"] == {
        "online": True,
        "on": True,
        "thermostatTemperatureSetpointHigh": -4.4,
        "thermostatTemperatureAmbient": -5,
        "thermostatMode": "heatcool",
        "thermostatTemperatureSetpointLow": -6.1,
        "currentFanSpeedSetting": "auto_low",
    }
    assert devices["climate.hvac"] == {
        "online": True,
        "on": True,
        "thermostatTemperatureSetpoint": -6.1,
        "thermostatTemperatureAmbient": -5.6,
        "thermostatMode": "cool",
        "thermostatHumidityAmbient": 54.2,
        "currentFanSpeedSetting": "on_high",
    }