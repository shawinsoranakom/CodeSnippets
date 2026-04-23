async def test_query_request(hass_fixture, assistant_client, auth_header) -> None:
    """Test a query request."""
    reqid = "5711642932632160984"
    data = {
        "requestId": reqid,
        "inputs": [
            {
                "intent": "action.devices.QUERY",
                "payload": {
                    "devices": [
                        {"id": "light.ceiling_lights"},
                        {"id": "light.bed_light"},
                        {"id": "light.kitchen_lights"},
                        {"id": "media_player.lounge_room"},
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
    assert len(devices) == 4
    assert devices["light.bed_light"]["on"] is False
    assert devices["light.ceiling_lights"]["on"] is True
    assert devices["light.ceiling_lights"]["brightness"] == 71
    assert devices["light.ceiling_lights"]["color"]["temperatureK"] == 2631
    assert devices["light.kitchen_lights"]["color"]["spectrumHsv"] == {
        "hue": 345,
        "saturation": 0.75,
        "value": 0.7058823529411765,
    }
    assert devices["media_player.lounge_room"]["on"] is True