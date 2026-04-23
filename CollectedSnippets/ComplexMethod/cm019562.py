async def test_multi_endpoint_entity_translation_key(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that multi-endpoint entities have a translation key and a name postfix.

    When a device has the same primary attribute on multiple endpoints,
    the entity name gets postfixed with the endpoint ID. The translation key
    must still always be set for translations.
    """
    # Endpoint 1
    entry_1 = entity_registry.async_get("light.inovelli_light_1")
    assert entry_1 is not None
    assert entry_1.translation_key == "light"
    assert entry_1.original_name == "Light (1)"

    state_1 = hass.states.get("light.inovelli_light_1")
    assert state_1 is not None
    assert state_1.name == "Inovelli Light (1)"

    # Endpoint 6
    entry_6 = entity_registry.async_get("light.inovelli_light_6")
    assert entry_6 is not None
    assert entry_6.translation_key == "light"
    assert entry_6.original_name == "Light (6)"

    state_6 = hass.states.get("light.inovelli_light_6")
    assert state_6 is not None
    assert state_6.name == "Inovelli Light (6)"