async def test_register_batched_platform_entity_service(
    hass: HomeAssistant,
) -> None:
    """Test registering a batched platform entity service."""
    calls: list[tuple[list[MockEntity], ServiceCall]] = []

    async def handle_service(
        batch_entities: list[MockEntity], call: ServiceCall
    ) -> None:
        calls.append((batch_entities, call))

    service.async_register_batched_platform_entity_service(
        hass,
        "mock_platform",
        "hello",
        entity_domain="mock_integration",
        schema={},
        func=handle_service,
        description_placeholders={"test_placeholder": "beer"},
    )
    descriptions = await service.async_get_all_descriptions(hass)
    assert descriptions["mock_platform"]["hello"]["description_placeholders"] == {
        "test_placeholder": "beer"
    }

    await hass.services.async_call(
        "mock_platform", "hello", {"entity_id": "all"}, blocking=True
    )
    assert calls == []

    entity_platform = MockEntityPlatform(
        hass, domain="mock_integration", platform_name="mock_platform", platform=None
    )
    entity1 = MockEntity(entity_id="mock_integration.entity1")
    entity2 = MockEntity(entity_id="mock_integration.entity2")
    await entity_platform.async_add_entities([entity1, entity2])

    await hass.services.async_call(
        "mock_platform", "hello", {"entity_id": entity1.entity_id}, blocking=True
    )
    assert len(calls) == 1
    assert calls[0][0] == [entity1]
    # Verify entity service fields are stripped from the ServiceCall
    assert calls[0][1].data == {}

    await hass.services.async_call(
        "mock_platform", "hello", {"entity_id": "all"}, blocking=True
    )
    assert len(calls) == 2
    assert calls[1][0] == unordered([entity1, entity2])