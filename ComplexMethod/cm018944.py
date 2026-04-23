async def test_media_player_playback(
    hass: HomeAssistant,
    setup_plex_server,
    requests_mock: requests_mock.Mocker,
    playqueue_created,
    player_plexhtpc_resources,
) -> None:
    """Test playing media on a Plex media_player."""
    requests_mock.get("http://1.2.3.6:32400/resources", text=player_plexhtpc_resources)

    await setup_plex_server()

    media_player = "media_player.plex_plex_htpc_for_mac_plex_htpc"
    requests_mock.post("/playqueues", text=playqueue_created)
    playmedia_mock = requests_mock.get(
        "/player/playback/playMedia", status_code=HTTPStatus.OK
    )

    # Test media lookup failure
    payload = '{"library_name": "Movies", "title": "Movie 1" }'
    with (
        patch(
            "plexapi.library.LibrarySection.search",
            return_value=None,
            __qualname__="search",
        ),
        pytest.raises(HomeAssistantError) as excinfo,
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
                ATTR_MEDIA_CONTENT_ID: payload,
            },
            True,
        )
    assert not playmedia_mock.called
    assert f"No {MediaType.MOVIE} results in 'Movies' for" in str(excinfo.value)

    movie1 = MockPlexMedia("Movie", "movie")
    movie2 = MockPlexMedia("Movie II", "movie")
    movie3 = MockPlexMedia("Movie III", "movie")

    # Test movie success
    movies = [movie1]
    with patch(
        "plexapi.library.LibrarySection.search",
        return_value=movies,
        __qualname__="search",
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
                ATTR_MEDIA_CONTENT_ID: '{"library_name": "Movies", "title": "Movie 1" }',
            },
            True,
        )
        assert playmedia_mock.called

    # Test movie success with resume
    playmedia_mock.reset()
    with patch(
        "plexapi.library.LibrarySection.search",
        return_value=movies,
        __qualname__="search",
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
                ATTR_MEDIA_CONTENT_ID: '{"library_name": "Movies", "title": "Movie 1", "resume": true}',
            },
            True,
        )
        assert playmedia_mock.called
        assert playmedia_mock.last_request.qs["offset"][0] == str(movie1.viewOffset)

    # Test movie success with media browser URL
    playmedia_mock.reset()
    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: media_player,
            ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
            ATTR_MEDIA_CONTENT_ID: PLEX_URI_SCHEME
            + f"{DEFAULT_DATA[CONF_SERVER_IDENTIFIER]}/1",
        },
        True,
    )
    assert playmedia_mock.called

    # Test movie success with media browser URL and resuming
    playmedia_mock.reset()
    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: media_player,
            ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
            ATTR_MEDIA_CONTENT_ID: PLEX_URI_SCHEME
            + f"{DEFAULT_DATA[CONF_SERVER_IDENTIFIER]}/1?resume=1",
        },
        True,
    )
    assert playmedia_mock.called
    assert playmedia_mock.last_request.qs["offset"][0] == "555"

    # Test movie success with legacy media browser URL
    playmedia_mock.reset()
    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: media_player,
            ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
            ATTR_MEDIA_CONTENT_ID: PLEX_URI_SCHEME + "1",
        },
        True,
    )
    assert playmedia_mock.called

    # Test multiple choices with exact match
    playmedia_mock.reset()
    movies = [movie1, movie2]
    with patch(
        "plexapi.library.LibrarySection.search",
        return_value=movies,
        __qualname__="search",
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
                ATTR_MEDIA_CONTENT_ID: '{"library_name": "Movies", "title": "Movie" }',
            },
            True,
        )
        assert playmedia_mock.called

    # Test multiple choices without exact match
    playmedia_mock.reset()
    movies = [movie2, movie3]
    with (
        pytest.raises(HomeAssistantError) as excinfo,
        patch(
            "plexapi.library.LibrarySection.search",
            return_value=movies,
            __qualname__="search",
        ),
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
                ATTR_MEDIA_CONTENT_ID: '{"library_name": "Movies", "title": "Movie" }',
            },
            True,
        )
    assert not playmedia_mock.called
    assert "Multiple matches, make content_id more specific" in str(excinfo.value)

    # Test multiple choices with allow_multiple
    movies = [movie1, movie2, movie3]
    with (
        patch(
            "plexapi.library.LibrarySection.search",
            return_value=movies,
            __qualname__="search",
        ),
        patch(
            "homeassistant.components.plex.server.PlexServer.create_playqueue"
        ) as mock_create_playqueue,
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {
                ATTR_ENTITY_ID: media_player,
                ATTR_MEDIA_CONTENT_TYPE: MediaType.MOVIE,
                ATTR_MEDIA_CONTENT_ID: '{"library_name": "Movies", "title": "Movie", "allow_multiple": true }',
            },
            True,
        )
        assert mock_create_playqueue.call_args.args == (movies,)
        assert playmedia_mock.called

    # Test radio station
    playmedia_mock.reset()
    radio_id = "/library/sections/3/stations/1"
    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: media_player,
            ATTR_MEDIA_CONTENT_TYPE: "station",
            ATTR_MEDIA_CONTENT_ID: PLEX_URI_SCHEME
            + f"{DEFAULT_DATA[CONF_SERVER_IDENTIFIER]}/{radio_id}",
        },
        True,
    )
    assert playmedia_mock.called