async def test_action_set_position(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_cover_entities: list[MockCover],
) -> None:
    """Test for cover set position actions."""
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
                        "event_type": "test_event_set_pos",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "set_position",
                        "position": 25,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_tilt_pos",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": "set_tilt_position",
                        "position": 75,
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()

    cover_pos_calls = async_mock_service(hass, "cover", "set_cover_position")
    tilt_pos_calls = async_mock_service(hass, "cover", "set_cover_tilt_position")

    hass.bus.async_fire("test_event_set_pos")
    await hass.async_block_till_done()
    assert len(cover_pos_calls) == 1
    assert len(tilt_pos_calls) == 0

    hass.bus.async_fire("test_event_set_tilt_pos")
    await hass.async_block_till_done()
    assert len(cover_pos_calls) == 1
    assert len(tilt_pos_calls) == 1

    assert cover_pos_calls[0].domain == DOMAIN
    assert cover_pos_calls[0].service == "set_cover_position"
    assert cover_pos_calls[0].data == {"entity_id": entry.entity_id, "position": 25}
    assert tilt_pos_calls[0].domain == DOMAIN
    assert tilt_pos_calls[0].service == "set_cover_tilt_position"
    assert tilt_pos_calls[0].data == {"entity_id": entry.entity_id, "tilt_position": 75}