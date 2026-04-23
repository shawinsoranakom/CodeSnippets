async def test_tv_load_and_unload(
    hass: HomeAssistant, mock_tv_config_entry: MockConfigEntry
) -> None:
    """Test loading and unloading TV entry."""
    await setup_integration(hass, mock_tv_config_entry)
    assert len(hass.states.async_entity_ids(Platform.MEDIA_PLAYER)) == 1
    assert DATA_APPS in hass.data

    assert await hass.config_entries.async_unload(mock_tv_config_entry.entry_id)
    await hass.async_block_till_done()
    entities = hass.states.async_entity_ids(Platform.MEDIA_PLAYER)
    assert len(entities) == 1
    for entity in entities:
        assert hass.states.get(entity).state == STATE_UNAVAILABLE
    assert DATA_APPS not in hass.data