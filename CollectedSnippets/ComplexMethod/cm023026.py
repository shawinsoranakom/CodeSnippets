async def test_intent_entity_remove_custom_name(
    hass: HomeAssistant,
    init_components,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that removing a custom name allows targeting the entity by its auto-generated name again."""
    context = Context()
    entity = MockLight("kitchen light", STATE_ON)
    entity._attr_unique_id = "1234"
    entity.entity_id = "light.kitchen"
    setup_test_component_platform(hass, LIGHT_DOMAIN, [entity])

    assert await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {LIGHT_DOMAIN: [{"platform": "test"}]},
    )
    await hass.async_block_till_done()

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    # Should fail with auto-generated name
    entity_registry.async_update_entity("light.kitchen", name="renamed light")
    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()
    assert data == snapshot
    assert data["response"]["response_type"] == "error"

    # Now clear the custom name
    entity_registry.async_update_entity("light.kitchen", name=None)
    await hass.async_block_till_done()

    result = await conversation.async_converse(
        hass, "turn on kitchen light", None, context
    )

    data = result.as_dict()

    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"
    assert len(calls) == 1

    result = await conversation.async_converse(
        hass, "turn on renamed light", None, context
    )

    data = result.as_dict()
    assert data == snapshot
    assert data["response"]["response_type"] == "error"