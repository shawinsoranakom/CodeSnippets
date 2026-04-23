async def test_execute_request(hass_fixture, assistant_client, auth_header) -> None:
    """Test an execute request."""
    reqid = "5711642932632160985"
    data = {
        "requestId": reqid,
        "inputs": [
            {
                "intent": "action.devices.EXECUTE",
                "payload": {
                    "commands": [
                        {
                            "devices": [
                                {"id": "light.ceiling_lights"},
                                {"id": "switch.decorative_lights"},
                                {"id": "media_player.lounge_room"},
                            ],
                            "execution": [
                                {
                                    "command": "action.devices.commands.OnOff",
                                    "params": {"on": False},
                                }
                            ],
                        },
                        {
                            "devices": [{"id": "media_player.walkman"}],
                            "execution": [
                                {
                                    "command": "action.devices.commands.setVolume",
                                    "params": {"volumeLevel": 70},
                                }
                            ],
                        },
                        {
                            "devices": [{"id": "light.kitchen_lights"}],
                            "execution": [
                                {
                                    "command": "action.devices.commands.ColorAbsolute",
                                    "params": {"color": {"spectrumRGB": 16711680}},
                                }
                            ],
                        },
                        {
                            "devices": [{"id": "light.bed_light"}],
                            "execution": [
                                {
                                    "command": "action.devices.commands.ColorAbsolute",
                                    "params": {"color": {"spectrumRGB": 65280}},
                                },
                                {
                                    "command": "action.devices.commands.ColorAbsolute",
                                    "params": {"color": {"temperature": 4700}},
                                },
                            ],
                        },
                        {
                            "devices": [{"id": "humidifier.humidifier"}],
                            "execution": [
                                {
                                    "command": "action.devices.commands.OnOff",
                                    "params": {"on": False},
                                }
                            ],
                        },
                        {
                            "devices": [{"id": "humidifier.dehumidifier"}],
                            "execution": [
                                {
                                    "command": "action.devices.commands.SetHumidity",
                                    "params": {"humidity": 45},
                                }
                            ],
                        },
                        {
                            "devices": [{"id": "humidifier.hygrostat"}],
                            "execution": [
                                {
                                    "command": "action.devices.commands.SetModes",
                                    "params": {"updateModeSettings": {"mode": "eco"}},
                                }
                            ],
                        },
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
    commands = body["payload"]["commands"]
    assert len(commands) == 9

    assert not any(result["status"] == "ERROR" for result in commands)

    ceiling = hass_fixture.states.get("light.ceiling_lights")
    assert ceiling.state == "off"

    kitchen = hass_fixture.states.get("light.kitchen_lights")
    assert kitchen.attributes.get(light.ATTR_RGB_COLOR) == (255, 0, 0)

    bed = hass_fixture.states.get("light.bed_light")
    assert bed.attributes.get(light.ATTR_COLOR_TEMP_KELVIN) == 4700

    assert hass_fixture.states.get("switch.decorative_lights").state == "off"

    walkman = hass_fixture.states.get("media_player.walkman")
    assert walkman.state == "playing"
    assert walkman.attributes.get(media_player.ATTR_MEDIA_VOLUME_LEVEL) == 0.7

    lounge = hass_fixture.states.get("media_player.lounge_room")
    assert lounge.state == "off"

    humidifier_state = hass_fixture.states.get("humidifier.humidifier")
    assert humidifier_state.state == "off"

    dehumidifier = hass_fixture.states.get("humidifier.dehumidifier")
    assert dehumidifier.attributes.get(humidifier.ATTR_HUMIDITY) == 45

    hygrostat = hass_fixture.states.get("humidifier.hygrostat")
    assert hygrostat.attributes.get(const.ATTR_MODE) == "eco"