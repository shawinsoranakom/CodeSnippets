async def test_error_duplicate_names(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test error message when multiple devices have the same name (or alias)."""
    kitchen_light_1 = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light_2 = entity_registry.async_get_or_create("light", "demo", "5678")

    # Same name and alias
    for light in (kitchen_light_1, kitchen_light_2):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="kitchen light",
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
            hass, f"turn on {name}", None, Context(), None
        )
        assert result.response.response_type == intent.IntentResponseType.ERROR
        assert (
            result.response.error_code
            == intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        assert (
            result.response.speech["plain"]["speech"]
            == f"Sorry, there are multiple devices called {name}"
        )

        # question
        result = await conversation.async_converse(
            hass, f"is {name} on?", None, Context(), None
        )
        assert result.response.response_type == intent.IntentResponseType.ERROR
        assert (
            result.response.error_code
            == intent.IntentResponseErrorCode.NO_VALID_TARGETS
        )
        assert (
            result.response.speech["plain"]["speech"]
            == f"Sorry, there are multiple devices called {name}"
        )