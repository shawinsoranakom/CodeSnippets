async def test_async_join_players_invalid(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    integration: None,
    mock_mozart_client: AsyncMock,
    mock_config_entry_core: MockConfigEntry,
    source: Source,
    group_members: list[str],
    expected_result: AbstractContextManager,
    error_type: str,
) -> None:
    """Test async_join_players with an invalid media_player entity."""
    source_change_callback = (
        mock_mozart_client.get_source_change_notifications.call_args[0][0]
    )

    mock_config_entry_core.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_core.entry_id)

    source_change_callback(source)

    with expected_result as exc_info:
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            SERVICE_JOIN,
            {
                ATTR_ENTITY_ID: TEST_MEDIA_PLAYER_ENTITY_ID,
                ATTR_GROUP_MEMBERS: group_members,
            },
            blocking=True,
        )

    assert exc_info.value.translation_domain == DOMAIN
    assert exc_info.value.translation_key == error_type
    assert exc_info.errisinstance(HomeAssistantError)

    assert mock_mozart_client.post_beolink_expand.call_count == 0
    assert mock_mozart_client.join_latest_beolink_experience.call_count == 0

    # Main entity
    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID))
    assert states == snapshot(exclude=props("media_position_updated_at"))

    # Secondary entity
    assert (states := hass.states.get(TEST_MEDIA_PLAYER_ENTITY_ID_2))
    assert states == snapshot(exclude=props("media_position_updated_at"))