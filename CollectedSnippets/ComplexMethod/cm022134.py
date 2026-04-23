async def test_get_events_with_device_ids(
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

    entry = MockConfigEntry(domain="test", data={"first": True}, options=None)
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        sw_version="sw-version",
        name="device name",
        manufacturer="manufacturer",
        model="model",
        suggested_area="Game Room",
    )

    class MockLogbookPlatform:
        """Mock a logbook platform."""

        @ha.callback
        def async_describe_events(
            hass: HomeAssistant,  # noqa: N805
            async_describe_event: Callable[
                [str, str, Callable[[Event], dict[str, str]]], None
            ],
        ) -> None:
            """Describe logbook events."""

            @ha.callback
            def async_describe_test_event(event: Event) -> dict[str, str]:
                """Describe mock logbook event."""
                return {
                    "name": "device name",
                    "message": "is on fire",
                }

            async_describe_event("test", "mock_event", async_describe_test_event)

    logbook._process_logbook_platform(hass, "test", MockLogbookPlatform)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire("mock_event", {"device_id": device.id})

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
    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
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
            "device_ids": [device.id],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["id"] == 1

    results = response["result"]
    assert len(results) == 1
    assert results[0]["name"] == "device name"
    assert results[0]["message"] == "is on fire"
    assert isinstance(results[0]["when"], float)

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
    assert len(results) == 4
    assert results[0]["message"] == "started"
    assert results[1]["name"] == "device name"
    assert results[1]["message"] == "is on fire"
    assert isinstance(results[1]["when"], float)
    assert results[2]["entity_id"] == "light.kitchen"
    assert results[2]["state"] == "on"
    assert isinstance(results[2]["when"], float)
    assert results[3]["entity_id"] == "light.kitchen"
    assert results[3]["state"] == "off"
    assert isinstance(results[3]["when"], float)