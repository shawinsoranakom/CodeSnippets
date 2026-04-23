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

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.PENDING)

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
                        "type": "triggered",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "triggered "
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
                        "type": "disarmed",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "disarmed "
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
                        "type": "armed_home",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "armed_home "
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
                        "type": "armed_away",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "armed_away "
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
                        "type": "armed_night",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "armed_night "
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
                        "type": "armed_vacation",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "armed_vacation "
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

    # Fake that the entity is triggered.
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.TRIGGERED)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert (
        service_calls[0].data["some"]
        == f"triggered - device - {entry.entity_id} - pending - triggered - None"
    )

    # Fake that the entity is disarmed.
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.DISARMED)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert (
        service_calls[1].data["some"]
        == f"disarmed - device - {entry.entity_id} - triggered - disarmed - None"
    )

    # Fake that the entity is armed home.
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_HOME)
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert (
        service_calls[2].data["some"]
        == f"armed_home - device - {entry.entity_id} - disarmed - armed_home - None"
    )

    # Fake that the entity is armed away.
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert (
        service_calls[3].data["some"]
        == f"armed_away - device - {entry.entity_id} - armed_home - armed_away - None"
    )

    # Fake that the entity is armed night.
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_NIGHT)
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    assert (
        service_calls[4].data["some"]
        == f"armed_night - device - {entry.entity_id} - armed_away - armed_night - None"
    )

    # Fake that the entity is armed vacation.
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_VACATION)
    await hass.async_block_till_done()
    assert len(service_calls) == 6
    assert (
        service_calls[5].data["some"]
        == f"armed_vacation - device - {entry.entity_id} - armed_night - armed_vacation - None"
    )