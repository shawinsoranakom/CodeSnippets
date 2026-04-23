async def test_event_entity_backup_completed(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test completed automatic backup event."""
    with patch("homeassistant.components.backup.PLATFORMS", [Platform.EVENT]):
        await setup_backup_integration(hass, with_hassio=False)
        await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("event.backup_automatic_backup")
    assert state.attributes[ATTR_EVENT_TYPE] is None

    client = await hass_ws_client(hass)
    await hass.async_block_till_done()
    await client.send_json_auto_id(
        {"type": "backup/generate", "agent_ids": ["backup.local"]}
    )
    assert await client.receive_json()

    state = hass.states.get("event.backup_automatic_backup")
    assert state.attributes[ATTR_EVENT_TYPE] == "in_progress"
    assert state.attributes[ATTR_BACKUP_STAGE] is not None
    assert state.attributes[ATTR_FAILED_REASON] is None

    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get("event.backup_automatic_backup")
    assert state.attributes[ATTR_EVENT_TYPE] == "completed"
    assert state.attributes[ATTR_BACKUP_STAGE] is None
    assert state.attributes[ATTR_FAILED_REASON] is None