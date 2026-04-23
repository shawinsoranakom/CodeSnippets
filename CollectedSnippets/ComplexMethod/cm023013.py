async def test_exposed_areas(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that all areas are exposed."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(kitchen_device.id, area_id=area_kitchen.id)

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id, device_id=kitchen_device.id
    )
    hass.states.async_set(
        kitchen_light.entity_id, "on", attributes={ATTR_FRIENDLY_NAME: "kitchen light"}
    )

    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id, area_id=area_bedroom.id
    )
    hass.states.async_set(
        bedroom_light.entity_id, "on", attributes={ATTR_FRIENDLY_NAME: "bedroom light"}
    )

    # Hide the bedroom light
    expose_entity(hass, bedroom_light.entity_id, False)

    result = await conversation.async_converse(
        hass, "turn on lights in the kitchen", None, Context(), None
    )

    # All is well for the exposed kitchen light
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert result.response.intent.slots["area"]["value"] == area_kitchen.id
    assert result.response.intent.slots["area"]["text"] == area_kitchen.normalized_name

    # Bedroom has no exposed entities
    result = await conversation.async_converse(
        hass, "turn on lights in the bedroom", None, Context(), None
    )

    # This should be an error because the lights in that area are not exposed
    assert result.response.response_type == intent.IntentResponseType.ERROR
    assert result.response.error_code == intent.IntentResponseErrorCode.NO_VALID_TARGETS

    # But we can still ask questions about the bedroom, even with no exposed entities
    result = await conversation.async_converse(
        hass, "how many lights are on in the bedroom?", None, Context(), None
    )
    assert result.response.response_type == intent.IntentResponseType.QUERY_ANSWER