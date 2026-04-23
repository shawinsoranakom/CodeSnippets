async def test_error_duplicate_names_same_area(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test error message when multiple devices have the same name (or alias) in the same area."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    kitchen_light_1 = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light_2 = entity_registry.async_get_or_create("light", "demo", "5678")

    # Same name and alias
    for light in (kitchen_light_1, kitchen_light_2):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="kitchen light",
            area_id=area_kitchen.id,
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    # Check name and alias
    for name in ("kitchen light", "overhead light"):
        # command
        result = await conversation.async_converse(
            hass, f"turn on {name} in {area_kitchen.name}", None, Context(), None
        )
        assert result.response.response_type == intent.IntentResponseType.ERROR
        assert (
            result.response.error_code
            == intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        assert (
            result.response.speech["plain"]["speech"]
            == f"Sorry, there are multiple devices called {name} in the {area_kitchen.name} area"
        )

        # question
        result = await conversation.async_converse(
            hass, f"is {name} on in the {area_kitchen.name}?", None, Context(), None
        )
        assert result.response.response_type == intent.IntentResponseType.ERROR
        assert (
            result.response.error_code
            == intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        assert (
            result.response.speech["plain"]["speech"]
            == f"Sorry, there are multiple devices called {name} in the {area_kitchen.name} area"
        )