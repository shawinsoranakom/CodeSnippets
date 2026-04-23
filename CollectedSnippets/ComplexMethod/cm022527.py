async def test_load_preferences(hass: HomeAssistant) -> None:
    """Make sure that we can load/save data correctly."""
    assert await async_setup_component(hass, "homeassistant", {})

    exposed_entities = hass.data[DATA_EXPOSED_ENTITIES]
    assert exposed_entities._assistants == {}
    assert exposed_entities.entities == {}

    exposed_entities.async_set_expose_new_entities("test1", True)
    exposed_entities.async_set_expose_new_entities("test2", False)

    async_expose_entity(hass, "test1", "light.kitchen", True)
    async_expose_entity(hass, "test1", "light.living_room", True)
    async_expose_entity(hass, "test2", "light.kitchen", True)
    async_expose_entity(hass, "test2", "light.kitchen", True)

    assert list(exposed_entities._assistants) == ["test1", "test2"]
    assert list(exposed_entities.entities) == ["light.kitchen", "light.living_room"]

    await flush_store(exposed_entities._store)

    exposed_entities2 = ExposedEntities(hass)
    await exposed_entities2.async_initialize()

    assert exposed_entities._assistants == exposed_entities2._assistants
    assert exposed_entities.entities == exposed_entities2.entities