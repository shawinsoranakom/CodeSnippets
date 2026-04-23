async def test_register_batched_entity_service(hass: HomeAssistant) -> None:
    """Test registering a batched entity service and calling it."""
    entity1 = MockEntity(entity_id=f"{DOMAIN}.entity1")
    entity2 = MockEntity(entity_id=f"{DOMAIN}.entity2")

    calls: list[tuple[list[MockEntity], ServiceCall]] = []

    async def handle_service(entities: list[MockEntity], call: ServiceCall) -> None:
        calls.append((entities, call))

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity1, entity2])

    component.async_register_batched_entity_service(
        "hello",
        {"some": str},
        handle_service,
        description_placeholders={"test_placeholder": "beer"},
    )
    descriptions = await async_get_all_descriptions(hass)
    assert descriptions[DOMAIN]["hello"]["description_placeholders"] == {
        "test_placeholder": "beer"
    }

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            "hello",
            {"entity_id": entity1.entity_id, "invalid": "data"},
            blocking=True,
        )
    assert len(calls) == 0

    await hass.services.async_call(
        DOMAIN,
        "hello",
        {"entity_id": entity1.entity_id, "some": "data"},
        blocking=True,
    )
    assert len(calls) == 1
    assert calls[0][0] == [entity1]
    # Verify entity service fields are stripped from the ServiceCall
    assert calls[0][1].data == {"some": "data"}

    await hass.services.async_call(
        DOMAIN,
        "hello",
        {"entity_id": ENTITY_MATCH_ALL, "some": "data"},
        blocking=True,
    )
    assert len(calls) == 2
    assert calls[1][0] == unordered([entity1, entity2])

    await hass.services.async_call(
        DOMAIN,
        "hello",
        {"entity_id": ENTITY_MATCH_NONE, "some": "data"},
        blocking=True,
    )
    assert len(calls) == 2