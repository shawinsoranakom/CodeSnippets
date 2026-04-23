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
                    "trigger": {"platform": "event", "event_type": "test_event_dock"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "dock",
                    },
                },
                {
                    "trigger": {"platform": "event", "event_type": "test_event_clean"},
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "clean",
                    },
                },
            ]
        },
    )

    dock_calls = async_mock_service(hass, "vacuum", "return_to_base")
    clean_calls = async_mock_service(hass, "vacuum", "start")

    hass.bus.async_fire("test_event_dock")
    await hass.async_block_till_done()
    assert len(dock_calls) == 1
    assert len(clean_calls) == 0

    hass.bus.async_fire("test_event_clean")
    await hass.async_block_till_done()
    assert len(dock_calls) == 1
    assert len(clean_calls) == 1

    assert dock_calls[-1].data == {"entity_id": entry.entity_id}
    assert clean_calls[-1].data == {"entity_id": entry.entity_id}