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
        entry.entity_id,
        STATE_ON,
        {
            const.ATTR_HUMIDITY: 23,
            const.ATTR_CURRENT_HUMIDITY: 35,
            ATTR_MODE: "home",
            const.ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_SUPPORTED_FEATURES: 1,
        },
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
                        "type": "target_humidity_changed",
                        "below": 20,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "target_humidity_changed_below"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "target_humidity_changed",
                        "above": 30,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "target_humidity_changed_above"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "target_humidity_changed",
                        "above": 30,
                        "for": {"seconds": 5},
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "target_humidity_changed_above_for"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_humidity_changed",
                        "below": 30,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_humidity_changed_below"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_humidity_changed",
                        "above": 40,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_humidity_changed_above"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "current_humidity_changed",
                        "above": 40,
                        "for": {"seconds": 5},
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "current_humidity_changed_above_for"},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
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
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
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
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
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

    # Fake that the humidity target is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 7, const.ATTR_CURRENT_HUMIDITY: 35},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "target_humidity_changed_below"

    # Fake that the current humidity is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 7, const.ATTR_CURRENT_HUMIDITY: 18},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "current_humidity_changed_below"

    # Fake that the humidity target is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 18},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "target_humidity_changed_above"

    # Fake that the current humidity is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 41},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].data["some"] == "current_humidity_changed_above"

    # Wait 6 minutes
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(minutes=6))
    await hass.async_block_till_done()
    assert len(service_calls) == 6
    assert {service_calls[4].data["some"], service_calls[5].data["some"]} == {
        "current_humidity_changed_above_for",
        "target_humidity_changed_above_for",
    }

    # Fake turn off
    hass.states.async_set(
        entry.entity_id,
        STATE_OFF,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 41},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 8
    assert {service_calls[6].data["some"], service_calls[7].data["some"]} == {
        "turn_off device - humidifier.test_5678 - on - off - None",
        "turn_on_or_off device - humidifier.test_5678 - on - off - None",
    }

    # Fake turn on
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 41},
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 10
    assert {service_calls[8].data["some"], service_calls[9].data["some"]} == {
        "turn_on device - humidifier.test_5678 - off - on - None",
        "turn_on_or_off device - humidifier.test_5678 - off - on - None",
    }