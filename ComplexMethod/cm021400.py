async def test_media_player_playing(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the Devialet configuration entry loading and unloading."""
    await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})
    entry = await setup_integration(hass, aioclient_mock)

    assert entry.state is ConfigEntryState.LOADED

    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: [f"{MP_DOMAIN}.{NAME.lower()}"]},
        blocking=True,
    )

    state = hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}")
    assert state.state == MediaPlayerState.PLAYING
    assert state.name == NAME
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == 0.2
    assert state.attributes[ATTR_MEDIA_VOLUME_MUTED] is False
    assert state.attributes[ATTR_INPUT_SOURCE_LIST] is not None
    assert state.attributes[ATTR_SOUND_MODE_LIST] is not None
    assert state.attributes[ATTR_MEDIA_ARTIST] == "The Beatles"
    assert state.attributes[ATTR_MEDIA_ALBUM_NAME] == "1 (Remastered)"
    assert state.attributes[ATTR_MEDIA_TITLE] == "Hey Jude - Remastered 2015"
    assert state.attributes[ATTR_ENTITY_PICTURE] is not None
    assert state.attributes[ATTR_MEDIA_DURATION] == 425653
    assert state.attributes[ATTR_MEDIA_POSITION] == 123102
    assert state.attributes[ATTR_MEDIA_POSITION_UPDATED_AT] is not None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] is not None
    assert state.attributes[ATTR_INPUT_SOURCE] is not None
    assert state.attributes[ATTR_SOUND_MODE] is not None

    with patch(
        "homeassistant.components.devialet.DevialetApi.playing_state",
        new_callable=PropertyMock,
    ) as mock:
        mock.return_value = MediaPlayerState.PAUSED

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert (
            hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").state
            == MediaPlayerState.PAUSED
        )

    with patch(
        "homeassistant.components.devialet.DevialetApi.playing_state",
        new_callable=PropertyMock,
    ) as mock:
        mock.return_value = MediaPlayerState.ON

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert (
            hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").state == MediaPlayerState.ON
        )

    with patch.object(DevialetApi, "equalizer", new_callable=PropertyMock) as mock:
        mock.return_value = None

        with patch.object(DevialetApi, "night_mode", new_callable=PropertyMock) as mock:
            mock.return_value = True

            await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
            assert (
                hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").attributes[
                    ATTR_SOUND_MODE
                ]
                == "Night mode"
            )

    with patch.object(DevialetApi, "equalizer", new_callable=PropertyMock) as mock:
        mock.return_value = "unexpected_value"

        with patch.object(DevialetApi, "night_mode", new_callable=PropertyMock) as mock:
            mock.return_value = False

            await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
            assert (
                ATTR_SOUND_MODE
                not in hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").attributes
            )

    with patch.object(DevialetApi, "equalizer", new_callable=PropertyMock) as mock:
        mock.return_value = None

        with patch.object(DevialetApi, "night_mode", new_callable=PropertyMock) as mock:
            mock.return_value = None

            await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
            assert (
                ATTR_SOUND_MODE
                not in hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").attributes
            )

    with patch.object(
        DevialetApi, "available_operations", new_callable=PropertyMock
    ) as mock:
        mock.return_value = None
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert (
            hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").attributes[
                ATTR_SUPPORTED_FEATURES
            ]
            == SUPPORT_DEVIALET
        )

    with patch.object(DevialetApi, "source", new_callable=PropertyMock) as mock:
        mock.return_value = "someSource"
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert (
            ATTR_INPUT_SOURCE
            not in hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}").attributes
        )

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED