async def test_automation_with_sub_condition(
    hass: HomeAssistant,
    service_calls: list[ServiceCall],
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test automation with device condition under and/or conditions."""
    LIGHT_DOMAIN = "light"

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry1 = entity_registry.async_get_or_create(
        "fake_integration", "test", "0001", device_id=device_entry.id
    )
    entity_entry2 = entity_registry.async_get_or_create(
        "fake_integration", "test", "0002", device_id=device_entry.id
    )

    hass.states.async_set(entity_entry1.entity_id, STATE_ON)
    hass.states.async_set(entity_entry2.entity_id, STATE_OFF)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "and",
                            "conditions": [
                                {
                                    "condition": "device",
                                    "domain": LIGHT_DOMAIN,
                                    "device_id": device_entry.id,
                                    "entity_id": entity_entry1.id,
                                    "type": "is_on",
                                },
                                {
                                    "condition": "device",
                                    "domain": LIGHT_DOMAIN,
                                    "device_id": device_entry.id,
                                    "entity_id": entity_entry2.id,
                                    "type": "is_on",
                                },
                            ],
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "and {{ trigger.platform }}"
                                " - {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": [
                        {
                            "condition": "or",
                            "conditions": [
                                {
                                    "condition": "device",
                                    "domain": LIGHT_DOMAIN,
                                    "device_id": device_entry.id,
                                    "entity_id": entity_entry1.id,
                                    "type": "is_on",
                                },
                                {
                                    "condition": "device",
                                    "domain": LIGHT_DOMAIN,
                                    "device_id": device_entry.id,
                                    "entity_id": entity_entry2.id,
                                    "type": "is_on",
                                },
                            ],
                        }
                    ],
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "or {{ trigger.platform }}"
                                " - {{ trigger.event.event_type }}"
                            )
                        },
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_entry1.entity_id).state == STATE_ON
    assert hass.states.get(entity_entry2.entity_id).state == STATE_OFF
    assert len(service_calls) == 0

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "or event - test_event1"

    hass.states.async_set(entity_entry1.entity_id, STATE_OFF)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    hass.states.async_set(entity_entry2.entity_id, STATE_ON)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "or event - test_event1"

    hass.states.async_set(entity_entry1.entity_id, STATE_ON)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert [service_calls[2].data["some"], service_calls[3].data["some"]] == unordered(
        ["or event - test_event1", "and event - test_event1"]
    )