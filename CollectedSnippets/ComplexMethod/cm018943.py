async def test_library_sensor_values(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
    setup_plex_server,
    mock_websocket,
    requests_mock: requests_mock.Mocker,
    library_movies_size,
    library_music_size,
    library_tvshows_size,
    library_tvshows_size_episodes,
    library_tvshows_size_seasons,
) -> None:
    """Test the library sensors."""
    requests_mock.get(
        "/library/sections/1/all?includeCollections=0",
        text=library_movies_size,
    )

    requests_mock.get(
        "/library/sections/2/all?includeCollections=0&type=2",
        text=library_tvshows_size,
    )
    requests_mock.get(
        "/library/sections/2/all?includeCollections=0&type=3",
        text=library_tvshows_size_seasons,
    )
    requests_mock.get(
        "/library/sections/2/all?includeCollections=0&type=4",
        text=library_tvshows_size_episodes,
    )

    requests_mock.get(
        "/library/sections/3/all?includeCollections=0",
        text=library_music_size,
    )

    mock_plex_server = await setup_plex_server()
    await wait_for_debouncer(hass)

    activity_sensor = hass.states.get("sensor.plex_server_1")
    assert activity_sensor.state == "1"

    # Ensure sensor is created as disabled
    assert hass.states.get("sensor.plex_server_1_library_tv_shows") is None

    # Enable sensor and validate values
    entity_registry.async_update_entity(
        entity_id="sensor.plex_server_1_library_tv_shows", disabled_by=None
    )
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )

    media = [MockPlexTVEpisode()]
    with patch(
        "plexapi.library.LibrarySection.recentlyAdded",
        return_value=media,
        __qualname__="recentlyAdded",
    ):
        await hass.async_block_till_done()

    library_tv_sensor = hass.states.get("sensor.plex_server_1_library_tv_shows")
    assert library_tv_sensor.state == "10"
    assert library_tv_sensor.attributes["seasons"] == 1
    assert library_tv_sensor.attributes["shows"] == 1
    assert (
        library_tv_sensor.attributes["last_added_item"]
        == "TV Show - S01E05 - Episode 5"
    )
    assert library_tv_sensor.attributes["last_added_timestamp"] == str(TIMESTAMP)

    # Handle `requests` exception
    requests_mock.get(
        "/library/sections/2/all?includeCollections=0&type=2",
        exc=requests.exceptions.ReadTimeout,
    )
    trigger_plex_update(
        mock_websocket, msgtype="status", payload=LIBRARY_UPDATE_PAYLOAD
    )
    await hass.async_block_till_done()

    library_tv_sensor = hass.states.get("sensor.plex_server_1_library_tv_shows")
    assert library_tv_sensor.state == STATE_UNAVAILABLE

    assert "Could not update library sensor" in caplog.text

    # Ensure sensor updates properly when it recovers
    requests_mock.get(
        "/library/sections/2/all?includeCollections=0&type=2",
        text=library_tvshows_size,
    )
    trigger_plex_update(
        mock_websocket, msgtype="status", payload=LIBRARY_UPDATE_PAYLOAD
    )
    with patch(
        "plexapi.library.LibrarySection.recentlyAdded",
        return_value=media,
        __qualname__="recentlyAdded",
    ):
        await hass.async_block_till_done()

    library_tv_sensor = hass.states.get("sensor.plex_server_1_library_tv_shows")
    assert library_tv_sensor.state == "10"

    # Handle library deletion
    requests_mock.get(
        "/library/sections/2/all?includeCollections=0&type=2",
        status_code=HTTPStatus.NOT_FOUND,
    )
    trigger_plex_update(
        mock_websocket, msgtype="status", payload=LIBRARY_UPDATE_PAYLOAD
    )
    await hass.async_block_till_done()

    library_tv_sensor = hass.states.get("sensor.plex_server_1_library_tv_shows")
    assert library_tv_sensor.state == STATE_UNAVAILABLE

    # Test movie library sensor
    entity_registry.async_update_entity(
        entity_id="sensor.plex_server_1_library_tv_shows",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    entity_registry.async_update_entity(
        entity_id="sensor.plex_server_1_library_movies", disabled_by=None
    )
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )

    media = [MockPlexMovie()]
    with patch(
        "plexapi.library.LibrarySection.recentlyAdded",
        return_value=media,
        __qualname__="recentlyAdded",
    ):
        await hass.async_block_till_done()

    library_movies_sensor = hass.states.get("sensor.plex_server_1_library_movies")
    assert library_movies_sensor.state == "1"
    assert library_movies_sensor.attributes["last_added_item"] == "Movie 1 (2021)"
    assert library_movies_sensor.attributes["last_added_timestamp"] == str(TIMESTAMP)

    # Test with clip
    media = [MockPlexClip()]
    with patch(
        "plexapi.library.LibrarySection.recentlyAdded",
        return_value=media,
        __qualname__="recentlyAdded",
    ):
        async_dispatcher_send(
            hass, PLEX_UPDATE_LIBRARY_SIGNAL.format(mock_plex_server.machine_identifier)
        )
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=3))
        await hass.async_block_till_done()

    library_movies_sensor = hass.states.get("sensor.plex_server_1_library_movies")
    assert library_movies_sensor.attributes["last_added_item"] == "Clip 1"

    # Test music library sensor
    entity_registry.async_update_entity(
        entity_id="sensor.plex_server_1_library_movies",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    entity_registry.async_update_entity(
        entity_id="sensor.plex_server_1_library_music", disabled_by=None
    )
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )

    media = [MockPlexMusic()]
    with patch(
        "plexapi.library.LibrarySection.recentlyAdded",
        return_value=media,
        __qualname__="recentlyAdded",
    ):
        await hass.async_block_till_done()

    library_music_sensor = hass.states.get("sensor.plex_server_1_library_music")
    assert library_music_sensor.state == "1"
    assert library_music_sensor.attributes["artists"] == 1
    assert library_music_sensor.attributes["albums"] == 1
    assert library_music_sensor.attributes["last_added_item"] == "Artist - Album (2021)"
    assert library_music_sensor.attributes["last_added_timestamp"] == str(TIMESTAMP)