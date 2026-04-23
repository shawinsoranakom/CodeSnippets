async def test_config_entry_unload(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_tts_entity: MockTTSEntity,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test we can unload config entry."""
    entity_id = f"{tts.DOMAIN}.{TEST_DOMAIN}"
    state = hass.states.get(entity_id)
    assert state is None

    config_entry = await mock_config_entry_setup(hass, mock_tts_entity)
    assert config_entry.state is ConfigEntryState.LOADED
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNKNOWN

    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)

    now = dt_util.utcnow()
    freezer.move_to(now)
    await hass.services.async_call(
        tts.DOMAIN,
        "speak",
        {
            ATTR_ENTITY_ID: entity_id,
            tts.ATTR_MEDIA_PLAYER_ENTITY_ID: "media_player.something",
            tts.ATTR_MESSAGE: "There is someone at the door.",
        },
        blocking=True,
    )
    assert len(calls) == 1

    assert (
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
        == HTTPStatus.OK
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == now.isoformat()

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED

    state = hass.states.get(entity_id)
    assert state is None