async def test_media_player_intents(
    hass: HomeAssistant,
    init_components,
) -> None:
    """Test pause/unpause/next/set volume for media players."""
    await media_player_intent.async_setup_intents(hass)

    entity_id = f"{media_player.DOMAIN}.tv"
    attributes = {
        ATTR_SUPPORTED_FEATURES: MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.VOLUME_SET
    }

    hass.states.async_set(entity_id, STATE_PLAYING, attributes=attributes)
    async_expose_entity(hass, conversation.DOMAIN, entity_id, True)

    # pause
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_PAUSE
    )
    result = await conversation.async_converse(hass, "pause tv", None, Context(), None)
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Paused"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # Unpause requires paused state
    hass.states.async_set(entity_id, STATE_PAUSED, attributes=attributes)

    # unpause
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_PLAY
    )
    result = await conversation.async_converse(
        hass, "unpause tv", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Resumed"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # Next track requires playing state
    hass.states.async_set(entity_id, STATE_PLAYING, attributes=attributes)

    # next
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_MEDIA_NEXT_TRACK
    )
    result = await conversation.async_converse(
        hass, "next item on tv", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Playing next"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # volume
    calls = async_mock_service(
        hass, media_player.DOMAIN, media_player.SERVICE_VOLUME_SET
    )
    result = await conversation.async_converse(
        hass, "set tv volume to 75 percent", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Volume set"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {
        "entity_id": entity_id,
        media_player.ATTR_MEDIA_VOLUME_LEVEL: 0.75,
    }