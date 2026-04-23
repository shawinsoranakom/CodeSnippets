async def test_async_update_beolink_listener(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    integration: None,
    mock_mozart_client: AsyncMock,
    mock_config_entry_core: MockConfigEntry,
) -> None:
    """Test _async_update_beolink as a listener."""
    playback_metadata_callback = (
        mock_mozart_client.get_playback_metadata_notifications.call_args[0][0]
    )

    # Add another entity
    mock_config_entry_core.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_core.entry_id)

    # Runs _async_update_beolink
    playback_metadata_callback(
        PlaybackContentMetadata(
            remote_leader=BeolinkLeader(
                friendly_name=TEST_FRIENDLY_NAME_2, jid=TEST_JID_2
            )
        )
    )

    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states.attributes["group_members"] == [
        TEST_MEDIA_PLAYER_ENTITY_ID_2,
        TEST_MEDIA_PLAYER_ENTITY_ID,
    ]

    # Called once for each entity during _initialize
    assert mock_mozart_client.get_beolink_listeners.call_count == 3
    # Called once for each entity during _initialize and
    # once more during _async_update_beolink for the entity that has the callback associated with it.
    assert mock_mozart_client.get_beolink_peers.call_count == 4

    # Main entity
    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states == snapshot(exclude=props("media_position_updated_at"))

    # Secondary entity
    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID_2))
    assert states == snapshot(exclude=props("media_position_updated_at"))