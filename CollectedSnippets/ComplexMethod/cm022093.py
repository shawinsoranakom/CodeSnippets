async def test_get_events_with_device_ids(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test logbook get_events for device ids."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    devices = await _async_mock_devices_with_logbook_platform(hass, device_registry)
    device = devices[0]
    device2 = devices[1]

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire("mock_event", {"device_id": device.id})
    hass.bus.async_fire("mock_event", {"device_id": device2.id})

    hass.states.async_set("light.kitchen", STATE_OFF)
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 100})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 200})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 300})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 400})
    await hass.async_block_till_done()
    context = core.Context(
        id="01GTDGKBCH00GW0X276W5TEDDD",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    hass.states.async_set("light.kitchen", STATE_OFF, context=context)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    client = await hass_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "device_ids": [device.id, device2.id],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 1

    results = response["result"]
    assert len(results) == 2
    assert results[0]["name"] == "device name"
    assert results[0]["message"] == "is on fire"
    assert isinstance(results[0]["when"], float)
    assert results[1]["name"] == "device name"
    assert results[1]["message"] == "is on fire"
    assert isinstance(results[1]["when"], float)

    await client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
            "device_ids": [device.id],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 2

    results = response["result"]
    assert results[0]["domain"] == "test"
    assert results[0]["message"] == "is on fire"
    assert results[0]["name"] == "device name"
    assert results[1]["entity_id"] == "light.kitchen"
    assert results[1]["state"] == "on"
    assert results[2]["entity_id"] == "light.kitchen"
    assert results[2]["state"] == "off"

    await client.send_json(
        {
            "id": 3,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 3

    results = response["result"]
    assert len(results) == 5
    assert results[0]["message"] == "started"
    assert results[1]["name"] == "device name"
    assert results[1]["message"] == "is on fire"
    assert isinstance(results[1]["when"], float)
    assert results[2]["name"] == "device name"
    assert results[2]["message"] == "is on fire"
    assert isinstance(results[2]["when"], float)
    assert results[3]["entity_id"] == "light.kitchen"
    assert results[3]["state"] == "on"
    assert isinstance(results[3]["when"], float)
    assert results[4]["entity_id"] == "light.kitchen"
    assert results[4]["state"] == "off"
    assert isinstance(results[4]["when"], float)