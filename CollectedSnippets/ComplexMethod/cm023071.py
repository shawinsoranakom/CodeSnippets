async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2", "option3"]}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_option_changed",
                        "to": "option2",
                    },
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "some": (
                                "to - {{ trigger.platform}} - "
                                "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                "{{ trigger.id}}"
                            )
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_option_changed",
                        "from": "option2",
                    },
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "some": (
                                "from - {{ trigger.platform}} - "
                                "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                "{{ trigger.id}}"
                            )
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_option_changed",
                        "from": "option3",
                        "to": "option1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "some": (
                                "from-to - {{ trigger.platform}} - "
                                "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                "{{ trigger.id}}"
                            )
                        },
                    },
                },
            ]
        },
    )

    # Test triggering device trigger with a to state
    hass.states.async_set(entry.entity_id, "option2")
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == f"to - device - {entry.entity_id} - option1 - option2 - None - 0"
    )

    # Test triggering device trigger with a from state
    hass.states.async_set(entry.entity_id, "option3")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"from - device - {entry.entity_id} - option2 - option3 - None - 0"
    )

    # Test triggering device trigger with both a from and to state
    hass.states.async_set(entry.entity_id, "option1")
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert (
        service_calls[2].data["some"]
        == f"from-to - device - {entry.entity_id} - option3 - option1 - None - 0"
    )