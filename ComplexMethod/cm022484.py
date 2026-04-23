async def test_execute_times_out(
    hass: HomeAssistant, light_only, report_state, on, brightness, value
) -> None:
    """Test an execute command which times out."""
    orig_execute_limit = sh.EXECUTE_LIMIT
    sh.EXECUTE_LIMIT = 0.02  # Decrease timeout to 20ms
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "light", {"light": {"platform": "demo"}})
    await hass.async_block_till_done()

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.ceiling_lights"}, blocking=True
    )
    await hass.async_block_till_done()

    events = async_capture_events(hass, EVENT_COMMAND_RECEIVED)
    service_events = async_capture_events(hass, EVENT_CALL_SERVICE)

    platforms = entity_platform.async_get_platforms(hass, "demo")
    assert platforms[0].domain == "light"
    assert platforms[0].entities["light.ceiling_lights"]

    turn_on_wait = asyncio.Event()

    async def slow_turn_on(*args, **kwargs):
        # Make DemoLigt.async_turn_on hang waiting for the turn_on_wait event
        await turn_on_wait.wait()

    with patch.object(DemoLight, "async_turn_on", wraps=slow_turn_on):
        result = await sh.async_handle_message(
            hass,
            MockConfig(should_report_state=report_state),
            None,
            None,
            {
                "requestId": REQ_ID,
                "inputs": [
                    {
                        "intent": "action.devices.EXECUTE",
                        "payload": {
                            "commands": [
                                {
                                    "devices": [
                                        {"id": "light.non_existing"},
                                        {"id": "light.ceiling_lights"},
                                        {"id": "light.kitchen_lights"},
                                    ],
                                    "execution": [
                                        {
                                            "command": "action.devices.commands.OnOff",
                                            "params": {"on": True},
                                        },
                                        {
                                            "command": "action.devices.commands.BrightnessAbsolute",
                                            "params": {"brightness": 20},
                                        },
                                    ],
                                }
                            ]
                        },
                    }
                ],
            },
            const.SOURCE_CLOUD,
        )

        turn_on_wait.set()
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    assert result == {
        "requestId": REQ_ID,
        "payload": {
            "commands": [
                {
                    "ids": ["light.non_existing"],
                    "status": "ERROR",
                    "errorCode": "deviceOffline",
                },
                {
                    "ids": ["light.ceiling_lights"],
                    "status": "SUCCESS",
                    "states": {
                        "on": on,
                        "online": True,
                    },
                },
                {
                    "ids": ["light.kitchen_lights"],
                    "status": "SUCCESS",
                    "states": {
                        "on": True,
                        "online": True,
                        "brightness": brightness,
                        "color": {
                            "spectrumHsv": {
                                "hue": 345,
                                "saturation": 0.75,
                                "value": value,
                            },
                        },
                    },
                },
            ]
        },
    }

    assert len(events) == 1
    assert events[0].event_type == EVENT_COMMAND_RECEIVED
    assert events[0].data == {
        "request_id": REQ_ID,
        "entity_id": [
            "light.non_existing",
            "light.ceiling_lights",
            "light.kitchen_lights",
        ],
        "execution": [
            {
                "command": "action.devices.commands.OnOff",
                "params": {"on": True},
            },
            {
                "command": "action.devices.commands.BrightnessAbsolute",
                "params": {"brightness": 20},
            },
        ],
        "source": "cloud",
    }

    service_events = sorted(
        service_events, key=lambda ev: ev.data["service_data"]["entity_id"]
    )
    assert len(service_events) == 4
    assert service_events[0].data == {
        "domain": "light",
        "service": "turn_on",
        "service_data": {"entity_id": "light.ceiling_lights"},
    }
    assert service_events[1].data == {
        "domain": "light",
        "service": "turn_on",
        "service_data": {"brightness_pct": 20, "entity_id": "light.ceiling_lights"},
    }
    assert service_events[0].context == events[0].context
    assert service_events[1].context == events[0].context
    assert service_events[2].data == {
        "domain": "light",
        "service": "turn_on",
        "service_data": {"entity_id": "light.kitchen_lights"},
    }
    assert service_events[3].data == {
        "domain": "light",
        "service": "turn_on",
        "service_data": {"brightness_pct": 20, "entity_id": "light.kitchen_lights"},
    }
    assert service_events[2].context == events[0].context
    assert service_events[3].context == events[0].context

    sh.EXECUTE_LIMIT = orig_execute_limit