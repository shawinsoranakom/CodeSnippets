async def test_cover_set_position(
    hass: HomeAssistant,
    init_components,
) -> None:
    """Test the open/close/set position for covers."""
    await cover_intent.async_setup_intents(hass)

    entity_id = f"{cover.DOMAIN}.garage_door"
    hass.states.async_set(entity_id, STATE_CLOSED)
    async_expose_entity(hass, conversation.DOMAIN, entity_id, True)

    # open
    calls = async_mock_service(hass, cover.DOMAIN, cover.SERVICE_OPEN_COVER)
    result = await conversation.async_converse(
        hass, "open the garage door", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Opening"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # close
    calls = async_mock_service(hass, cover.DOMAIN, cover.SERVICE_CLOSE_COVER)
    result = await conversation.async_converse(
        hass, "close garage door", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Closing"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # set position
    calls = async_mock_service(hass, cover.DOMAIN, cover.SERVICE_SET_COVER_POSITION)
    result = await conversation.async_converse(
        hass, "set garage door to 50%", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Position set"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id, cover.ATTR_POSITION: 50}