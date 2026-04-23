async def test_async_entity_ids_count(hass: HomeAssistant) -> None:
    """Test async_entity_ids_count."""

    assert hass.states.async_entity_ids_count() == 0
    assert hass.states.async_entity_ids_count("light") == 0
    assert hass.states.async_entity_ids_count({"light", "vacuum"}) == 0

    hass.states.async_set("switch.link", "on")
    hass.states.async_set("light.bowl", "on")
    hass.states.async_set("light.frog", "on")
    hass.states.async_set("vacuum.floor", "on")

    assert hass.states.async_entity_ids_count() == 4
    assert hass.states.async_entity_ids_count("light") == 2

    hass.states.async_set("light.cow", "on")

    assert hass.states.async_entity_ids_count() == 5
    assert hass.states.async_entity_ids_count("light") == 3
    assert hass.states.async_entity_ids_count({"light", "vacuum"}) == 4