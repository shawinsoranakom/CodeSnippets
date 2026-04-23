async def test_unexposed_entities_skipped(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that unexposed entities are skipped in exposed areas."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    # Both lights are in the kitchen
    exposed_light = entity_registry.async_get_or_create("light", "demo", "1234")
    exposed_light = entity_registry.async_update_entity(
        exposed_light.entity_id,
        area_id=area_kitchen.id,
    )
    hass.states.async_set(exposed_light.entity_id, "off")

    unexposed_light = entity_registry.async_get_or_create("light", "demo", "5678")
    unexposed_light = entity_registry.async_update_entity(
        unexposed_light.entity_id,
        area_id=area_kitchen.id,
    )
    hass.states.async_set(unexposed_light.entity_id, "off")

    # On light is exposed, the other is not
    expose_entity(hass, exposed_light.entity_id, True)
    expose_entity(hass, unexposed_light.entity_id, False)

    # Only one light should be turned on
    calls = async_mock_service(hass, "light", "turn_on")
    result = await conversation.async_converse(
        hass, "turn on kitchen lights", None, Context(), None
    )

    assert len(calls) == 1
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert result.response.intent.slots["area"]["value"] == area_kitchen.id
    assert result.response.intent.slots["area"]["text"] == area_kitchen.normalized_name

    # Only one light should be returned
    hass.states.async_set(exposed_light.entity_id, "on")
    hass.states.async_set(unexposed_light.entity_id, "on")
    result = await conversation.async_converse(
        hass, "how many lights are on in the kitchen", None, Context(), None
    )

    assert result.response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(result.response.matched_states) == 1
    assert result.response.matched_states[0].entity_id == exposed_light.entity_id