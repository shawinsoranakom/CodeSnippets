async def test_action(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test for lock actions."""
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
                    "trigger": {"platform": "event", "event_type": "test_event_lock"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "lock",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_unlock"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "unlock",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_open"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "open",
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()

    lock_calls = async_mock_service(hass, "lock", "lock")
    unlock_calls = async_mock_service(hass, "lock", "unlock")
    open_calls = async_mock_service(hass, "lock", "open")

    hass.bus.async_fire("test_event_lock")
    await hass.async_block_till_done()
    assert len(lock_calls) == 1
    assert len(unlock_calls) == 0
    assert len(open_calls) == 0

    hass.bus.async_fire("test_event_unlock")
    await hass.async_block_till_done()
    assert len(lock_calls) == 1
    assert len(unlock_calls) == 1
    assert len(open_calls) == 0

    hass.bus.async_fire("test_event_open")
    await hass.async_block_till_done()
    assert len(lock_calls) == 1
    assert len(unlock_calls) == 1
    assert len(open_calls) == 1

    assert lock_calls[0].domain == DOMAIN
    assert lock_calls[0].service == "lock"
    assert lock_calls[0].data == {"entity_id": entry.entity_id}
    assert unlock_calls[0].domain == DOMAIN
    assert unlock_calls[0].service == "unlock"
    assert unlock_calls[0].data == {"entity_id": entry.entity_id}
    assert open_calls[0].domain == DOMAIN
    assert open_calls[0].service == "open"
    assert open_calls[0].data == {"entity_id": entry.entity_id}