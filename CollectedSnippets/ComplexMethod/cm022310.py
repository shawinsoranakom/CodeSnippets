async def test_hue_events(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_bridge_v1: Mock,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test that hue remotes fire events when pressed."""
    mock_bridge_v1.mock_sensor_responses.append(SENSOR_RESPONSE)

    events = async_capture_events(hass, ATTR_HUE_EVENT)

    await setup_platform(
        hass, mock_bridge_v1, [Platform.BINARY_SENSOR, Platform.SENSOR]
    )
    assert len(mock_bridge_v1.mock_requests) == 1
    assert len(hass.states.async_all()) == 7
    assert len(events) == 0

    hue_tap_device = device_registry.async_get_device(
        identifiers={(hue.DOMAIN, "00:00:00:00:00:44:23:08")}
    )

    mock_bridge_v1.api.sensors["7"].last_event = {"type": "button"}
    mock_bridge_v1.api.sensors["8"].last_event = {"type": "button"}

    new_sensor_response = dict(SENSOR_RESPONSE)
    new_sensor_response["7"] = dict(new_sensor_response["7"])
    new_sensor_response["7"]["state"] = {
        "buttonevent": 18,
        "lastupdated": "2019-12-28T22:58:03",
    }
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    freezer.tick(sensor_base.SensorManager.SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 2
    assert len(hass.states.async_all()) == 7
    assert len(events) == 1
    assert events[-1].data == {
        "device_id": hue_tap_device.id,
        "id": "hue_tap",
        "unique_id": "00:00:00:00:00:44:23:08-f2",
        "event": 18,
        "last_updated": "2019-12-28T22:58:03",
    }

    hue_dimmer_device = device_registry.async_get_device(
        identifiers={(hue.DOMAIN, "00:17:88:01:10:3e:3a:dc")}
    )

    new_sensor_response = dict(new_sensor_response)
    new_sensor_response["8"] = dict(new_sensor_response["8"])
    new_sensor_response["8"]["state"] = {
        "buttonevent": 3002,
        "lastupdated": "2019-12-28T22:58:03",
    }
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    freezer.tick(sensor_base.SensorManager.SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 3
    assert len(hass.states.async_all()) == 7
    assert len(events) == 2
    assert events[-1].data == {
        "device_id": hue_dimmer_device.id,
        "id": "hue_dimmer_switch_1",
        "unique_id": "00:17:88:01:10:3e:3a:dc-02-fc00",
        "event": 3002,
        "last_updated": "2019-12-28T22:58:03",
    }

    # Fire old event, it should be ignored
    new_sensor_response = dict(new_sensor_response)
    new_sensor_response["8"] = dict(new_sensor_response["8"])
    new_sensor_response["8"]["state"] = {
        "buttonevent": 18,
        "lastupdated": "2019-12-28T22:58:02",
    }
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    freezer.tick(sensor_base.SensorManager.SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 4
    assert len(hass.states.async_all()) == 7
    assert len(events) == 2

    # Add a new remote. In discovery the new event is registered **but not fired**
    new_sensor_response = dict(new_sensor_response)
    new_sensor_response["21"] = {
        "state": {
            "rotaryevent": 2,
            "expectedrotation": 208,
            "expectedeventduration": 400,
            "lastupdated": "2020-01-31T15:56:19",
        },
        "swupdate": {"state": "noupdates", "lastinstall": "2019-11-26T03:35:21"},
        "config": {"on": True, "battery": 100, "reachable": True, "pending": []},
        "name": "Lutron Aurora 1",
        "type": "ZLLRelativeRotary",
        "modelid": "Z3-1BRL",
        "manufacturername": "Lutron",
        "productname": "Lutron Aurora",
        "diversityid": "2c3a75ff-55c4-4e4d-8c44-82d330b8eb9b",
        "swversion": "3.4",
        "uniqueid": "ff:ff:00:0f:e7:fd:bc:b7-01-fc00-0014",
        "capabilities": {
            "certified": True,
            "primary": True,
            "inputs": [
                {
                    "repeatintervals": [400],
                    "events": [
                        {"rotaryevent": 1, "eventtype": "start"},
                        {"rotaryevent": 2, "eventtype": "repeat"},
                    ],
                }
            ],
        },
    }
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    freezer.tick(sensor_base.SensorManager.SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(mock_bridge_v1.mock_requests) == 5
    assert len(hass.states.async_all()) == 8
    assert len(events) == 2

    # A new press fires the event
    new_sensor_response["21"]["state"]["lastupdated"] = "2020-01-31T15:57:19"
    mock_bridge_v1.mock_sensor_responses.append(new_sensor_response)

    # Force updates to run again
    freezer.tick(sensor_base.SensorManager.SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    hue_aurora_device = device_registry.async_get_device(
        identifiers={(hue.DOMAIN, "ff:ff:00:0f:e7:fd:bc:b7")}
    )

    assert len(mock_bridge_v1.mock_requests) == 6
    assert len(hass.states.async_all()) == 8
    assert len(events) == 3
    assert events[-1].data == {
        "device_id": hue_aurora_device.id,
        "id": "lutron_aurora_1",
        "unique_id": "ff:ff:00:0f:e7:fd:bc:b7-01-fc00-0014",
        "event": 2,
        "last_updated": "2020-01-31T15:57:19",
    }