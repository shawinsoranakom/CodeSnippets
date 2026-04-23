async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for turn_on and turn_off triggers firing.

    This is a sanity test for the toggle entity device automation helper, this is
    tested by each integration too.
    """
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        "switch", "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_ON)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": "switch",
                        "device_id": device_entry.id,
                        "entity_id": entry.entity_id,
                        "type": "turned_on",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "turn_on {{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": "switch",
                        "device_id": device_entry.id,
                        "entity_id": entry.entity_id,
                        "type": "turned_off",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "turn_off {{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                            )
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": "switch",
                        "device_id": device_entry.id,
                        "entity_id": entry.entity_id,
                        "type": "changed_states",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "turn_on_or_off {{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                            )
                        },
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()
    assert hass.states.get(entry.entity_id).state == STATE_ON
    assert len(service_calls) == 0

    hass.states.async_set(entry.entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert {service_calls[0].data["some"], service_calls[1].data["some"]} == {
        f"turn_off device - {entry.entity_id} - on - off - None",
        f"turn_on_or_off device - {entry.entity_id} - on - off - None",
    }

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert {service_calls[2].data["some"], service_calls[3].data["some"]} == {
        f"turn_on device - {entry.entity_id} - off - on - None",
        f"turn_on_or_off device - {entry.entity_id} - off - on - None",
    }