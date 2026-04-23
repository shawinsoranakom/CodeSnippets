async def test_download_switch(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, nzbget_api: MagicMock
) -> None:
    """Test the creation and values of the download switch."""
    instance = nzbget_api.return_value

    entry = await init_integration(hass)
    assert entry

    entity_id = "switch.nzbgettest_download"
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.unique_id == f"{entry.entry_id}_download"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON

    # test download paused
    instance.status.return_value["DownloadPaused"] = True

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF