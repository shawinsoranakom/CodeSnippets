async def test_same_named_entities_in_different_areas(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that entities with the same name in different areas can be targeted."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    # Both lights have the same name, but are in different areas
    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        area_id=area_kitchen.id,
        name="overhead light",
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )

    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id,
        area_id=area_bedroom.id,
        name="overhead light",
    )
    hass.states.async_set(
        bedroom_light.entity_id,
        "off",
        attributes={ATTR_FRIENDLY_NAME: bedroom_light.name},
    )

    # Target kitchen light
    calls = async_mock_service(hass, "light", "turn_on")
    result = await conversation.async_converse(
        hass, "turn on overhead light in the kitchen", None, Context(), None
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert (
        result.response.intent.slots.get("name", {}).get("value") == kitchen_light.name
    )
    assert (
        result.response.intent.slots.get("name", {}).get("text") == kitchen_light.name
    )
    assert len(result.response.matched_states) == 1
    assert result.response.matched_states[0].entity_id == kitchen_light.entity_id
    assert calls[0].data.get("entity_id") == [kitchen_light.entity_id]

    # Target bedroom light
    calls.clear()
    result = await conversation.async_converse(
        hass, "turn on overhead light in the bedroom", None, Context(), None
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert (
        result.response.intent.slots.get("name", {}).get("value") == bedroom_light.name
    )
    assert (
        result.response.intent.slots.get("name", {}).get("text") == bedroom_light.name
    )
    assert len(result.response.matched_states) == 1
    assert result.response.matched_states[0].entity_id == bedroom_light.entity_id
    assert calls[0].data.get("entity_id") == [bedroom_light.entity_id]

    # Targeting a duplicate name should fail
    result = await conversation.async_converse(
        hass, "turn on overhead light", None, Context(), None
    )
    assert result.response.response_type == intent.IntentResponseType.ERROR

    # Querying a duplicate name should also fail
    result = await conversation.async_converse(
        hass, "is the overhead light on?", None, Context(), None
    )
    assert result.response.response_type == intent.IntentResponseType.ERROR

    # But we can still ask questions that don't rely on the name
    result = await conversation.async_converse(
        hass, "how many lights are on?", None, Context(), None
    )
    assert result.response.response_type == intent.IntentResponseType.QUERY_ANSWER