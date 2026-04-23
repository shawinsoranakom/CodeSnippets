async def test_intent_entity_added_removed(
    hass: HomeAssistant,
    init_components,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test processing intent via HTTP API with entities added later.

    We want to ensure that adding an entity later busts the cache
    so that the new entity is available as well as any aliases.
    """
    context = Context()
    entity_registry.async_get_or_create(
        "light", "demo", "1234", suggested_object_id="kitchen"
    )
    entity_registry.async_update_entity(
        "light.kitchen", aliases=[er.COMPUTED_NAME, "my cool light"]
    )
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", "off")

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")
    result = await conversation.async_converse(
        hass, "turn on my cool light", None, context
    )

    assert len(calls) == 1
    data = result.as_dict()

    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"

    # Add an entity
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "5678",
        suggested_object_id="late",
        original_name="friendly light",
    )
    hass.states.async_set("light.late", "off", {"friendly_name": "friendly light"})

    result = await conversation.async_converse(
        hass, "turn on friendly light", None, context
    )
    data = result.as_dict()

    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"

    # Now add an alias
    entity_registry.async_update_entity(
        "light.late", aliases=[er.COMPUTED_NAME, "late added light"]
    )

    result = await conversation.async_converse(
        hass, "turn on late added light", None, context
    )

    data = result.as_dict()

    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"

    # Now delete the entity
    hass.states.async_remove("light.late")

    result = await conversation.async_converse(
        hass, "turn on late added light", None, context
    )
    data = result.as_dict()
    assert data == snapshot
    assert data["response"]["response_type"] == "error"