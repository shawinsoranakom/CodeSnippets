async def test_nabu_casa_zwa2(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    nabu_casa_zwa2: Node,
    integration: MockConfigEntry,
) -> None:
    """Test ZWA-2 discovery."""
    state = hass.states.get("light.home_assistant_connect_zwa_2_led")
    assert state, "The LED indicator should be enabled by default"

    entry = entity_registry.async_get(state.entity_id)
    assert entry, "Entity for the LED indicator not found"

    assert entry.capabilities.get(ATTR_SUPPORTED_COLOR_MODES) == [
        ColorMode.ONOFF,
    ], "The LED indicator should be an ON/OFF light"

    assert not entry.disabled, "The entity should be enabled by default"

    assert entry.entity_category is EntityCategory.CONFIG, (
        "The LED indicator should be configuration"
    )

    # Test that the entity name is properly set to "LED"
    assert entry.original_name == "LED", (
        "The LED entity should have the original name 'LED'"
    )
    assert state.attributes["friendly_name"] == "Home Assistant Connect ZWA-2 LED", (
        "The LED should have the correct friendly name"
    )