async def test_action(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test for actions."""
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
        {const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_turn_off",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "turn_off",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_turn_on",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "turn_on",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_toggle"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "toggle",
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_humidity",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "set_humidity",
                        "humidity": 35,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_mode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "set_mode",
                        "mode": const.MODE_AWAY,
                    },
                },
            ]
        },
    )

    set_humidity_calls = async_mock_service(hass, "humidifier", "set_humidity")
    set_mode_calls = async_mock_service(hass, "humidifier", "set_mode")
    turn_on_calls = async_mock_service(hass, "humidifier", "turn_on")
    turn_off_calls = async_mock_service(hass, "humidifier", "turn_off")
    toggle_calls = async_mock_service(hass, "humidifier", "toggle")

    assert len(set_humidity_calls) == 0
    assert len(set_mode_calls) == 0
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_set_humidity")
    await hass.async_block_till_done()
    assert len(set_humidity_calls) == 1
    assert len(set_mode_calls) == 0
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_set_mode")
    await hass.async_block_till_done()
    assert len(set_humidity_calls) == 1
    assert len(set_mode_calls) == 1
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_turn_off")
    await hass.async_block_till_done()
    assert len(set_humidity_calls) == 1
    assert len(set_mode_calls) == 1
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 1
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_turn_on")
    await hass.async_block_till_done()
    assert len(set_humidity_calls) == 1
    assert len(set_mode_calls) == 1
    assert len(turn_on_calls) == 1
    assert len(turn_off_calls) == 1
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_toggle")
    await hass.async_block_till_done()
    assert len(set_humidity_calls) == 1
    assert len(set_mode_calls) == 1
    assert len(turn_on_calls) == 1
    assert len(turn_off_calls) == 1
    assert len(toggle_calls) == 1

    assert set_humidity_calls[0].domain == DOMAIN
    assert set_humidity_calls[0].service == "set_humidity"
    assert set_humidity_calls[0].data == {"entity_id": entry.entity_id, "humidity": 35}
    assert set_mode_calls[0].domain == DOMAIN
    assert set_mode_calls[0].service == "set_mode"
    assert set_mode_calls[0].data == {"entity_id": entry.entity_id, "mode": "away"}
    assert turn_on_calls[0].domain == DOMAIN
    assert turn_on_calls[0].service == "turn_on"
    assert turn_on_calls[0].data == {"entity_id": entry.entity_id}
    assert turn_off_calls[0].domain == DOMAIN
    assert turn_off_calls[0].service == "turn_off"
    assert turn_off_calls[0].data == {"entity_id": entry.entity_id}
    assert toggle_calls[0].domain == DOMAIN
    assert toggle_calls[0].service == "toggle"
    assert toggle_calls[0].data == {"entity_id": entry.entity_id}