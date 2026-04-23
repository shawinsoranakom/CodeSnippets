async def test_if_state(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, CoverState.OPEN)

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
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_open",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_open "
                                "- {{ trigger.platform }} "
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
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_closed",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_closed "
                                "- {{ trigger.platform }} "
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
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_opening",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_opening "
                                "- {{ trigger.platform }} "
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
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_closing",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_closing "
                                "- {{ trigger.platform }} "
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
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "is_open - event - test_event1"

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "is_closed - event - test_event2"

    hass.states.async_set(entry.entity_id, CoverState.OPENING)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "is_opening - event - test_event3"

    hass.states.async_set(entry.entity_id, CoverState.CLOSING)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].data["some"] == "is_closing - event - test_event4"