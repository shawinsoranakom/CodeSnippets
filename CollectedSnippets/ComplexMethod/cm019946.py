async def test_action(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test for turn_on and turn_off actions."""
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
                    "trigger": {"platform": "event", "event_type": "test_off"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "turn_off",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_on"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "turn_on",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_toggle"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "toggle",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_flash_short"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "flash",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_flash_long"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "flash",
                        "flash": "long",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_brightness_increase",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "brightness_increase",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_brightness_decrease",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "brightness_decrease",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_brightness"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "turn_on",
                        "brightness_pct": 75,
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()

    turn_on_calls = async_mock_service(hass, DOMAIN, "turn_on")
    turn_off_calls = async_mock_service(hass, DOMAIN, "turn_off")
    toggle_calls = async_mock_service(hass, DOMAIN, "toggle")

    hass.bus.async_fire("test_toggle")
    await hass.async_block_till_done()
    assert len(toggle_calls) == 1
    assert toggle_calls[-1].data == {"entity_id": entry.entity_id}

    hass.bus.async_fire("test_off")
    await hass.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert turn_off_calls[-1].data == {"entity_id": entry.entity_id}

    hass.bus.async_fire("test_brightness_increase")
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 1
    assert turn_on_calls[-1].data == {
        "entity_id": entry.entity_id,
        "brightness_step_pct": 10,
    }

    hass.bus.async_fire("test_brightness_decrease")
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 2
    assert turn_on_calls[-1].data == {
        "entity_id": entry.entity_id,
        "brightness_step_pct": -10,
    }

    hass.bus.async_fire("test_brightness")
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 3
    assert turn_on_calls[-1].data == {
        "entity_id": entry.entity_id,
        "brightness_pct": 75,
    }

    hass.bus.async_fire("test_on")
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 4
    assert turn_on_calls[-1].data == {"entity_id": entry.entity_id}

    hass.bus.async_fire("test_flash_short")
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 5
    assert turn_on_calls[-1].data == {
        "entity_id": entry.entity_id,
        "flash": FLASH_SHORT,
    }

    hass.bus.async_fire("test_flash_long")
    await hass.async_block_till_done()
    assert len(turn_on_calls) == 6
    assert turn_on_calls[-1].data == {"entity_id": entry.entity_id, "flash": FLASH_LONG}