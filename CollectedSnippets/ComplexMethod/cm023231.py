async def test_node_status_state(
    hass: HomeAssistant,
    client,
    lock_schlage_be469,
    integration,
    service_calls: list[ServiceCall],
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test for node_status conditions."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, lock_schlage_be469)}
    )
    assert device

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device.id,
                            "type": "node_status",
                            "status": "alive",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "alive - {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device.id,
                            "type": "node_status",
                            "status": "awake",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "awake - {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event3"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device.id,
                            "type": "node_status",
                            "status": "asleep",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "asleep - {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event4"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device.id,
                            "type": "node_status",
                            "status": "dead",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "dead - {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
            ]
        },
    )

    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "alive - event - test_event1"

    event = Event(
        "wake up",
        data={
            "source": "node",
            "event": "wake up",
            "nodeId": lock_schlage_be469.node_id,
        },
    )
    lock_schlage_be469.receive_event(event)
    await hass.async_block_till_done()

    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "awake - event - test_event2"

    event = Event(
        "sleep",
        data={"source": "node", "event": "sleep", "nodeId": lock_schlage_be469.node_id},
    )
    lock_schlage_be469.receive_event(event)
    await hass.async_block_till_done()

    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "asleep - event - test_event3"

    event = Event(
        "dead",
        data={"source": "node", "event": "dead", "nodeId": lock_schlage_be469.node_id},
    )
    lock_schlage_be469.receive_event(event)
    await hass.async_block_till_done()

    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].data["some"] == "dead - event - test_event4"