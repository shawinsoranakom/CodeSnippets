async def test_updates_from_players_changed_new_ids(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    config_entry: MockConfigEntry,
    controller: MockHeos,
    change_data_mapped_ids: PlayerUpdateResult,
) -> None:
    """Test player updates from changes to available players."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)

    # Assert device registry matches current id
    assert device_registry.async_get_device(identifiers={(DOMAIN, "1")})
    # Assert entity registry matches current id
    assert (
        entity_registry.async_get_entity_id(MEDIA_PLAYER_DOMAIN, DOMAIN, "1")
        == "media_player.test_player"
    )

    await controller.dispatcher.wait_send(
        SignalType.CONTROLLER_EVENT,
        const.EVENT_PLAYERS_CHANGED,
        change_data_mapped_ids,
    )
    await hass.async_block_till_done()

    # Assert device registry identifiers were updated
    assert len(device_registry.devices) == 2
    assert device_registry.async_get_device(identifiers={(DOMAIN, "101")})
    # Assert entity registry unique id was updated
    assert len(entity_registry.entities) == 2
    assert (
        entity_registry.async_get_entity_id(MEDIA_PLAYER_DOMAIN, DOMAIN, "101")
        == "media_player.test_player"
    )