async def test_vacuum_intents(
    hass: HomeAssistant,
    init_components,
) -> None:
    """Test start/return to base for vacuums."""
    await vaccum_intent.async_setup_intents(hass)

    entity_id = f"{vacuum.DOMAIN}.rover"
    hass.states.async_set(
        entity_id,
        STATE_CLOSED,
        {
            ATTR_SUPPORTED_FEATURES: vacuum.VacuumEntityFeature.START
            | vacuum.VacuumEntityFeature.RETURN_HOME
        },
    )
    async_expose_entity(hass, conversation.DOMAIN, entity_id, True)

    # start
    calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_START)
    result = await conversation.async_converse(
        hass, "start rover", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Started"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}

    # return to base
    calls = async_mock_service(hass, vacuum.DOMAIN, vacuum.SERVICE_RETURN_TO_BASE)
    result = await conversation.async_converse(
        hass, "return rover to base", None, Context(), None
    )
    await hass.async_block_till_done()

    response = result.response
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.speech["plain"]["speech"] == "Returning"
    assert len(calls) == 1
    call = calls[0]
    assert call.data == {"entity_id": entity_id}