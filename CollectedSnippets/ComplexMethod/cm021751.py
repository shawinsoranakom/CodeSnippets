async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for state triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)

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
                        "type": "opened",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "opened "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
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
                        "type": "closed",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "closed "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
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
                        "type": "opening",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "opening "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
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
                        "type": "closing",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "closing "
                                "- {{ trigger.platform }} "
                                "- {{ trigger.entity_id }} "
                                "- {{ trigger.from_state.state }} "
                                "- {{ trigger.to_state.state }} "
                                "- {{ trigger.for }}"
                            )
                        },
                    },
                },
            ]
        },
    )

    # Fake that the entity is opened.
    hass.states.async_set(entry.entity_id, CoverState.OPEN)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == f"opened - device - {entry.entity_id} - closed - open - None"
    )

    # Fake that the entity is closed.
    hass.states.async_set(entry.entity_id, CoverState.CLOSED)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"closed - device - {entry.entity_id} - open - closed - None"
    )

    # Fake that the entity is opening.
    hass.states.async_set(entry.entity_id, CoverState.OPENING)
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert (
        service_calls[2].data["some"]
        == f"opening - device - {entry.entity_id} - closed - opening - None"
    )

    # Fake that the entity is closing.
    hass.states.async_set(entry.entity_id, CoverState.CLOSING)
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert (
        service_calls[3].data["some"]
        == f"closing - device - {entry.entity_id} - opening - closing - None"
    )