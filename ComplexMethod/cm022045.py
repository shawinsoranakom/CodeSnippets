async def test_if_state(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for all conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

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
                            "type": "is_triggered",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_triggered "
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
                            "type": "is_disarmed",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_disarmed "
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
                            "type": "is_armed_home",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_armed_home "
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
                            "type": "is_armed_away",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_armed_away "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event5"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_armed_night",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_armed_night "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event6"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_armed_vacation",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_armed_vacation "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event7"},
                    "condition": [
                        {
                            "condition": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "is_armed_custom_bypass",
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "is_armed_custom_bypass "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
            ]
        },
    )
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.TRIGGERED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "is_triggered - event - test_event1"

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.DISARMED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "is_disarmed - event - test_event2"

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_HOME)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "is_armed_home - event - test_event3"

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_AWAY)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].data["some"] == "is_armed_away - event - test_event4"

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_NIGHT)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    assert service_calls[4].data["some"] == "is_armed_night - event - test_event5"

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_VACATION)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 6
    assert service_calls[5].data["some"] == "is_armed_vacation - event - test_event6"

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_CUSTOM_BYPASS)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    assert len(service_calls) == 7
    assert (
        service_calls[6].data["some"] == "is_armed_custom_bypass - event - test_event7"
    )