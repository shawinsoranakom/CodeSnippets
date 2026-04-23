async def test_register_entity_service(
    hass: HomeAssistant,
    schema: dict | None,
    service_data: dict,
) -> None:
    """Test registering an entity service and calling it."""
    entity = MockEntity(entity_id=f"{DOMAIN}.entity")
    calls = []

    @callback
    def appender(**kwargs):
        calls.append(kwargs)

    entity.async_called_by_service = appender

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})
    await component.async_add_entities([entity])

    component.async_register_entity_service(
        "hello",
        schema,
        "async_called_by_service",
        description_placeholders={"test_placeholder": "beer"},
    )
    descriptions = await async_get_all_descriptions(hass)
    assert descriptions["test_domain"]["hello"]["description_placeholders"] == {
        "test_placeholder": "beer"
    }

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN,
            "hello",
            {"entity_id": entity.entity_id, "invalid": "data"},
            blocking=True,
        )
    assert len(calls) == 0

    await hass.services.async_call(
        DOMAIN, "hello", {"entity_id": entity.entity_id} | service_data, blocking=True
    )
    assert len(calls) == 1
    assert calls[0] == service_data

    await hass.services.async_call(
        DOMAIN, "hello", {"entity_id": ENTITY_MATCH_ALL} | service_data, blocking=True
    )
    assert len(calls) == 2
    assert calls[1] == service_data

    await hass.services.async_call(
        DOMAIN, "hello", {"entity_id": ENTITY_MATCH_NONE} | service_data, blocking=True
    )
    assert len(calls) == 2

    await hass.services.async_call(
        DOMAIN, "hello", {"area_id": ENTITY_MATCH_NONE} | service_data, blocking=True
    )
    assert len(calls) == 2