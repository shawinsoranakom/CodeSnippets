async def test_media_player_receives_push_updates(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Test the Android TV Remote media player receives push updates and state is updated."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={"apps": {"com.google.android.youtube.tv": {"app_name": "YouTube"}}},
    )
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    mock_api._on_is_on_updated(False)
    assert hass.states.is_state(MEDIA_PLAYER_ENTITY, STATE_OFF)

    mock_api._on_is_on_updated(True)
    assert hass.states.is_state(MEDIA_PLAYER_ENTITY, STATE_ON)

    mock_api._on_current_app_updated("com.google.android.tvlauncher")
    assert (
        hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("app_id")
        == "com.google.android.tvlauncher"
    )
    assert (
        hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("app_name")
        == "com.google.android.tvlauncher"
    )

    mock_api._on_current_app_updated("com.google.android.youtube.tv")
    assert (
        hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("app_id")
        == "com.google.android.youtube.tv"
    )
    assert hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("app_name") == "YouTube"

    mock_api._on_volume_info_updated({"level": 35, "muted": False, "max": 100})
    assert hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("volume_level") == 0.35

    mock_api._on_volume_info_updated({"level": 50, "muted": True, "max": 100})
    assert hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("volume_level") == 0.50
    assert hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("is_volume_muted")

    mock_api._on_volume_info_updated({"level": 0, "muted": False, "max": 0})
    assert hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("volume_level") is None
    assert (
        hass.states.get(MEDIA_PLAYER_ENTITY).attributes.get("is_volume_muted") is None
    )

    mock_api._on_is_available_updated(False)
    assert hass.states.is_state(MEDIA_PLAYER_ENTITY, STATE_UNAVAILABLE)

    mock_api._on_is_available_updated(True)
    assert hass.states.is_state(MEDIA_PLAYER_ENTITY, STATE_ON)