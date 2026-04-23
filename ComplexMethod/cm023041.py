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
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_toggle",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "toggle",
                    },
                },
            ]
        },
    )

    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    toggle_calls = async_mock_service(hass, "fan", "toggle")

    hass.bus.async_fire("test_event_turn_off")
    await hass.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert turn_off_calls[0].data["entity_id"] == entry.entity_id
    assert len(turn_on_calls) == 0
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_turn_on")
    await hass.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].data["entity_id"] == entry.entity_id
    assert len(toggle_calls) == 0

    hass.bus.async_fire("test_event_toggle")
    await hass.async_block_till_done()
    assert len(turn_off_calls) == 1
    assert len(turn_on_calls) == 1
    assert len(toggle_calls) == 1
    assert toggle_calls[0].data["entity_id"] == entry.entity_id