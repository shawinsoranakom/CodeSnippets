async def test_if_fires_on_state_change_with_for(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for triggers firing with delay."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, LockState.UNLOCKED)

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
                        "type": "locked",
                        "for": {"seconds": 5},
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
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "unlocking",
                        "for": {"seconds": 5},
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
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "jammed",
                        "for": {"seconds": 5},
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
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "locking",
                        "for": {"seconds": 5},
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
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "opening",
                        "for": {"seconds": 5},
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
            ]
        },
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    hass.states.async_set(entry.entity_id, LockState.LOCKED)
    await hass.async_block_till_done()
    assert len(service_calls) == 0
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    await hass.async_block_till_done()
    assert (
        service_calls[0].data["some"]
        == f"turn_off device - {entry.entity_id} - unlocked - locked - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.UNLOCKING)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=16))
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    await hass.async_block_till_done()
    assert (
        service_calls[1].data["some"]
        == f"turn_on device - {entry.entity_id} - locked - unlocking - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.JAMMED)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=21))
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    await hass.async_block_till_done()
    assert (
        service_calls[2].data["some"]
        == f"turn_off device - {entry.entity_id} - unlocking - jammed - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.LOCKING)
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=27))
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    await hass.async_block_till_done()
    assert (
        service_calls[3].data["some"]
        == f"turn_on device - {entry.entity_id} - jammed - locking - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.OPENING)
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=27))
    await hass.async_block_till_done()
    assert len(service_calls) == 5
    await hass.async_block_till_done()
    assert (
        service_calls[4].data["some"]
        == f"turn_on device - {entry.entity_id} - locking - opening - 0:00:05"
    )