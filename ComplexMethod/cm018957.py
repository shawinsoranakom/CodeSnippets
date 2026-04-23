async def test_new_ignored_users_available(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    entry,
    mock_websocket,
    setup_plex_server,
    requests_mock: requests_mock.Mocker,
    session_new_user,
) -> None:
    """Test setting up when new users available on Plex server but are ignored."""
    MONITORED_USERS = {"User 1": {"enabled": True}}
    OPTIONS_WITH_USERS = copy.deepcopy(DEFAULT_OPTIONS)
    OPTIONS_WITH_USERS[Platform.MEDIA_PLAYER][CONF_MONITORED_USERS] = MONITORED_USERS
    OPTIONS_WITH_USERS[Platform.MEDIA_PLAYER][CONF_IGNORE_NEW_SHARED_USERS] = True
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, options=OPTIONS_WITH_USERS)

    mock_plex_server = await setup_plex_server(config_entry=entry)

    requests_mock.get(
        f"{mock_plex_server.url_in_use}/status/sessions",
        text=session_new_user,
    )
    trigger_plex_update(mock_websocket)
    await wait_for_debouncer(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    server_id = mock_plex_server.machine_identifier

    active_sessions = mock_plex_server._plex_server.sessions()
    monitored_users = hass.data[DOMAIN][SERVERS][server_id].option_monitored_users
    ignored_users = [x for x in mock_plex_server.accounts if x not in monitored_users]

    assert len(monitored_users) == 1
    assert len(ignored_users) == 2

    for ignored_user in ignored_users:
        ignored_client = [
            x.players[0] for x in active_sessions if x.usernames[0] == ignored_user
        ]
        if ignored_client:
            assert (
                f"Ignoring {ignored_client[0].product} client owned by '{ignored_user}'"
                in caplog.text
            )

    await wait_for_debouncer(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    sensor = hass.states.get("sensor.plex_server_1")
    assert sensor.state == str(len(active_sessions))