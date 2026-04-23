async def test_not_adding_duplicate_entities_with_unique_id(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test for not adding duplicate entities.

    Also test that the entity registry is not updated for duplicates.
    """
    caplog.set_level(logging.ERROR)
    component = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup({})

    ent1 = MockEntity(name="test1", unique_id="not_very_unique")
    await component.async_add_entities([ent1])

    assert len(hass.states.async_entity_ids()) == 1
    assert not caplog.text

    ent2 = MockEntity(name="test2", unique_id="not_very_unique")
    await component.async_add_entities([ent2])
    assert "test1" in caplog.text
    assert DOMAIN in caplog.text

    ent3 = MockEntity(
        name="test2", entity_id="test_domain.test3", unique_id="not_very_unique"
    )
    await component.async_add_entities([ent3])
    assert "test1" in caplog.text
    assert "test3" in caplog.text
    assert DOMAIN in caplog.text

    assert ent2.hass is None
    assert ent2.platform is None
    assert len(hass.states.async_entity_ids()) == 1

    # test the entity name was not updated
    entry = entity_registry.async_get_or_create(DOMAIN, DOMAIN, "not_very_unique")
    assert entry.original_name == "test1"