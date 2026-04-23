async def test_check_attributes(
    hass: HomeAssistant,
    mock_now: dt_util.dt.datetime,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test attributes."""
    await setup_integration(hass, aioclient_mock)

    state = hass.states.get(MAIN_ENTITY_ID)
    assert state.state == STATE_PLAYING

    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) == "17016356"
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.MOVIE
    assert state.attributes.get(ATTR_MEDIA_DURATION) == 7200
    assert state.attributes.get(ATTR_MEDIA_POSITION) == 4437
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT)
    assert state.attributes.get(ATTR_MEDIA_TITLE) == "Snow Bride"
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_CHANNEL) == "HALLHD (312)"
    assert state.attributes.get(ATTR_INPUT_SOURCE) == "312"
    assert not state.attributes.get(ATTR_MEDIA_CURRENTLY_RECORDING)
    assert state.attributes.get(ATTR_MEDIA_RATING) == "TV-G"
    assert not state.attributes.get(ATTR_MEDIA_RECORDED)
    assert state.attributes.get(ATTR_MEDIA_START_TIME) == datetime(
        2020, 3, 21, 13, 0, tzinfo=dt_util.UTC
    )

    state = hass.states.get(CLIENT_ENTITY_ID)
    assert state.state == STATE_PLAYING

    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) == "4405732"
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.TVSHOW
    assert state.attributes.get(ATTR_MEDIA_DURATION) == 1791
    assert state.attributes.get(ATTR_MEDIA_POSITION) == 263
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT)
    assert state.attributes.get(ATTR_MEDIA_TITLE) == "Tyler's Ultimate"
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) == "Spaghetti and Clam Sauce"
    assert state.attributes.get(ATTR_MEDIA_CHANNEL) == "FOODHD (231)"
    assert state.attributes.get(ATTR_INPUT_SOURCE) == "231"
    assert not state.attributes.get(ATTR_MEDIA_CURRENTLY_RECORDING)
    assert state.attributes.get(ATTR_MEDIA_RATING) == "No Rating"
    assert state.attributes.get(ATTR_MEDIA_RECORDED)
    assert state.attributes.get(ATTR_MEDIA_START_TIME) == datetime(
        2010, 7, 5, 15, 0, 8, tzinfo=dt_util.UTC
    )

    state = hass.states.get(MUSIC_ENTITY_ID)
    assert state.state == STATE_PLAYING

    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) == "76917562"
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) == MediaType.MUSIC
    assert state.attributes.get(ATTR_MEDIA_DURATION) == 86400
    assert state.attributes.get(ATTR_MEDIA_POSITION) == 15050
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT)
    assert state.attributes.get(ATTR_MEDIA_TITLE) == "Sparkle In Your Eyes"
    assert state.attributes.get(ATTR_MEDIA_ARTIST) == "Gerald Albright"
    assert state.attributes.get(ATTR_MEDIA_ALBUM_NAME) == "Slam Dunk (2014)"
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_CHANNEL) == "MCSJ (851)"
    assert state.attributes.get(ATTR_INPUT_SOURCE) == "851"
    assert not state.attributes.get(ATTR_MEDIA_CURRENTLY_RECORDING)
    assert state.attributes.get(ATTR_MEDIA_RATING) == "TV-PG"
    assert not state.attributes.get(ATTR_MEDIA_RECORDED)
    assert state.attributes.get(ATTR_MEDIA_START_TIME) == datetime(
        2020, 3, 21, 10, 0, 0, tzinfo=dt_util.UTC
    )

    state = hass.states.get(STANDBY_ENTITY_ID)
    assert state.state == STATE_OFF

    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) is None
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) is None
    assert state.attributes.get(ATTR_MEDIA_DURATION) is None
    assert state.attributes.get(ATTR_MEDIA_POSITION) is None
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT) is None
    assert state.attributes.get(ATTR_MEDIA_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_ARTIST) is None
    assert state.attributes.get(ATTR_MEDIA_ALBUM_NAME) is None
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_CHANNEL) is None
    assert state.attributes.get(ATTR_INPUT_SOURCE) is None
    assert not state.attributes.get(ATTR_MEDIA_CURRENTLY_RECORDING)
    assert state.attributes.get(ATTR_MEDIA_RATING) is None
    assert not state.attributes.get(ATTR_MEDIA_RECORDED)

    state = hass.states.get(RESTRICTED_ENTITY_ID)
    assert state.state == STATE_PLAYING

    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) is None
    assert state.attributes.get(ATTR_MEDIA_CONTENT_TYPE) is None
    assert state.attributes.get(ATTR_MEDIA_DURATION) is None
    assert state.attributes.get(ATTR_MEDIA_POSITION) is None
    assert state.attributes.get(ATTR_MEDIA_POSITION_UPDATED_AT) is None
    assert state.attributes.get(ATTR_MEDIA_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_ARTIST) is None
    assert state.attributes.get(ATTR_MEDIA_ALBUM_NAME) is None
    assert state.attributes.get(ATTR_MEDIA_SERIES_TITLE) is None
    assert state.attributes.get(ATTR_MEDIA_CHANNEL) is None
    assert state.attributes.get(ATTR_INPUT_SOURCE) is None
    assert not state.attributes.get(ATTR_MEDIA_CURRENTLY_RECORDING)
    assert state.attributes.get(ATTR_MEDIA_RATING) is None
    assert not state.attributes.get(ATTR_MEDIA_RECORDED)

    state = hass.states.get(UNAVAILABLE_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE