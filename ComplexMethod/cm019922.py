async def test_remote_receives_push_updates(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Test the Android TV Remote receives push updates and state is updated."""
    new_options = {"apps": {"com.google.android.youtube.tv": {"app_name": "YouTube"}}}
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    mock_api._on_is_on_updated(False)
    assert hass.states.is_state(REMOTE_ENTITY, STATE_OFF)

    mock_api._on_is_on_updated(True)
    assert hass.states.is_state(REMOTE_ENTITY, STATE_ON)

    mock_api._on_current_app_updated("activity1")
    assert (
        hass.states.get(REMOTE_ENTITY).attributes.get("current_activity") == "activity1"
    )

    mock_api._on_current_app_updated("com.google.android.youtube.tv")
    assert (
        hass.states.get(REMOTE_ENTITY).attributes.get("current_activity") == "YouTube"
    )

    mock_api._on_is_available_updated(False)
    assert hass.states.is_state(REMOTE_ENTITY, STATE_UNAVAILABLE)

    mock_api._on_is_available_updated(True)
    assert hass.states.is_state(REMOTE_ENTITY, STATE_ON)