async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    mock_bridge_v1: Mock,
    device_registry: dr.DeviceRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for button press trigger firing."""
    mock_bridge_v1.mock_sensor_responses.append(REMOTES_RESPONSE)
    await setup_platform(
        hass, mock_bridge_v1, [Platform.SENSOR, Platform.BINARY_SENSOR]
    )
    assert len(mock_bridge_v1.mock_requests) == 1
    assert len(hass.states.async_all()) == 1

    # Set an automation with a specific tap switch trigger
    hue_tap_device = device_registry.async_get_device(
        identifiers={(hue.DOMAIN, "00:00:00:00:00:44:23:08")}
    )
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": hue.DOMAIN,
                        "device_id": hue_tap_device.id,
                        "type": "remote_button_short_press",
                        "subtype": "button_4",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "B4 - {{ trigger.event.data.event }}"
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": hue.DOMAIN,
                        "device_id": "mock-device-id",
                        "type": "remote_button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "B1 - {{ trigger.event.data.event }}"
                        },
                    },
                },
            ]
        },
    )

    # Fake that the remote is being pressed.
    new_sensor_response = dict(REMOTES_RESPONSE)
    new_sensor_response["7"] = dict(new_sensor_response["7"])
    new_sensor_response["7"]["state"] = {
        "buttonevent": 18,
        "lastupdated": "2019-12-28T22:58:02",
    }
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge_v1.sensor_manager.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 2

    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "B4 - 18"

    # Fake another button press.
    new_sensor_response["7"] = dict(new_sensor_response["7"])
    new_sensor_response["7"]["state"] = {
        "buttonevent": 34,
        "lastupdated": "2019-12-28T22:58:05",
    }
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    await mock_bridge_v1.sensor_manager.coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(mock_bridge_v1.mock_requests) == 3
    assert len(service_calls) == 1