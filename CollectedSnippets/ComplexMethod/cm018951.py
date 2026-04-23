async def test_option_flow_new_users_available(
    hass: HomeAssistant, entry, setup_plex_server
) -> None:
    """Test config options multiselect defaults when new Plex users are seen."""
    OPTIONS_OWNER_ONLY = copy.deepcopy(DEFAULT_OPTIONS)
    OPTIONS_OWNER_ONLY[Platform.MEDIA_PLAYER][CONF_MONITORED_USERS] = {
        "User 1": {"enabled": True}
    }
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, options=OPTIONS_OWNER_ONLY)

    mock_plex_server = await setup_plex_server(config_entry=entry)
    await hass.async_block_till_done()

    server_id = "unique_id_123"
    monitored_users = hass.data[DOMAIN][SERVERS][server_id].option_monitored_users

    new_users = [x for x in mock_plex_server.accounts if x not in monitored_users]
    assert len(monitored_users) == 1
    assert len(new_users) == 2

    result = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "plex_mp_settings"
    multiselect_defaults = result["data_schema"].schema["monitored_users"].options

    assert "[Owner]" in multiselect_defaults["User 1"]
    for user in new_users:
        assert "[New]" in multiselect_defaults[user]