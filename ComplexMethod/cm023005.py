async def test_valve_intents(
    hass: HomeAssistant,
    init_components,
) -> None:
    """Test open/close/set position for valves."""
    entity_id = f"{valve.DOMAIN}.main_valve"
    hass.states.async_set(entity_id, STATE_CLOSED)
    async_expose_entity(hass, conversation.DOMAIN, entity_id, True)

    # open
    calls = async_mock_service(hass, valve.DOMAIN, valve.SERVICE_OPEN_VALVE)
    result = await conversation.async_converse(
        hass, "open the main valve", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Opening"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # close
    calls = async_mock_service(hass, valve.DOMAIN, valve.SERVICE_CLOSE_VALVE)
    result = await conversation.async_converse(
        hass, "close main valve", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Closing"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # set position
    calls = async_mock_service(hass, valve.DOMAIN, valve.SERVICE_SET_VALVE_POSITION)
    result = await conversation.async_converse(
        hass, "set main valve position to 25", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Position set"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id, valve.ATTR_POSITION: 25}