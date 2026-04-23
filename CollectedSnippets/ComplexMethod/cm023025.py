async def test_intent_alias_added_removed(
    hass: HomeAssistant,
    init_components,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test processing intent via HTTP API with aliases added later.

    We want to ensure that adding an alias later busts the cache
    so that the new alias is available.
    """
    context = Context()
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "1234",
        suggested_object_id="kitchen",
        original_name="kitchen light",
    )
    hass.states.async_set("light.kitchen", "off", {"friendly_name": "kitchen light"})

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )
    assert len(calls) == 1
    data = result.as_dict()

    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"

    # Add an alias
    entity_registry.async_update_entity(
        "light.kitchen", aliases=[er.COMPUTED_NAME, "late added alias"]
    )

    result = await conversation.async_converse(
        hass, "turn on late added alias", None, context
    )

    data = result.as_dict()

    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"

    # Now remove the alias
    entity_registry.async_update_entity("light.kitchen", aliases=[er.COMPUTED_NAME])

    result = await conversation.async_converse(
        hass, "turn on late added alias", None, context
    )

    data = result.as_dict()
    assert data == snapshot
    assert data["response"]["response_type"] == "error"