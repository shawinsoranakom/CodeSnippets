async def test_turn_on_intent(
    hass: HomeAssistant,
    init_components,
    conversation_id,
    sentence,
    agent_id,
    snapshot: SnapshotAssertion,
) -> None:
    """Test calling the turn on intent."""
    hass.states.async_set("light.kitchen", "off")
    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    data = {conversation.ATTR_TEXT: sentence}
    if agent_id is not None:
        data[conversation.ATTR_AGENT_ID] = agent_id
    if conversation_id is not None:
        data[conversation.ATTR_CONVERSATION_ID] = conversation_id
    result = await hass.services.async_call(
        "conversation",
        "process",
        data,
        blocking=True,
        return_response=True,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call.domain == LIGHT_DOMAIN
    assert call.service == "turn_on"
    assert call.data == {"entity_id": ["light.kitchen"]}

    assert result == snapshot