async def test_update_state(hass: HomeAssistant, mock_device: MagicMock) -> None:
    """Tests dispatched signals update player."""
    entity = hass.states.get(ENTITY_ID)
    assert entity is not None
    assert entity.state == STATE_OFF

    # Device turns on
    mock_device.power.state = kaleidescape_const.DEVICE_POWER_STATE_ON
    mock_device.dispatcher.send(kaleidescape_const.DEVICE_POWER_STATE)
    await hass.async_block_till_done()
    entity = hass.states.get(ENTITY_ID)
    assert entity is not None
    assert entity.state == STATE_IDLE

    # Devices starts playing
    mock_device.movie = Movie(
        handle="handle",
        title="title",
        cover="cover",
        cover_hires="cover_hires",
        rating="rating",
        rating_reason="rating_reason",
        year="year",
        runtime="runtime",
        actors=[],
        director="director",
        directors=[],
        genre="genre",
        genres=[],
        synopsis="synopsis",
        color="color",
        country="country",
        aspect_ratio="aspect_ratio",
        media_type="media_type",
        play_status=kaleidescape_const.PLAY_STATUS_PLAYING,
        play_speed=1,
        title_number=1,
        title_length=1,
        title_location=1,
        chapter_number=1,
        chapter_length=1,
        chapter_location=1,
    )
    mock_device.dispatcher.send(kaleidescape_const.PLAY_STATUS)
    await hass.async_block_till_done()
    entity = hass.states.get(ENTITY_ID)
    assert entity is not None
    assert entity.state == STATE_PLAYING

    # Devices pauses playing
    mock_device.movie.play_status = kaleidescape_const.PLAY_STATUS_PAUSED
    mock_device.dispatcher.send(kaleidescape_const.PLAY_STATUS)
    await hass.async_block_till_done()
    entity = hass.states.get(ENTITY_ID)
    assert entity is not None
    assert entity.state == STATE_PAUSED