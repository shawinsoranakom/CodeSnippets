async def test_extraction_functions_unknown_script(hass: HomeAssistant) -> None:
    """Test extraction functions for an unknown script."""
    assert await async_setup_component(hass, DOMAIN, {})
    assert script.labels_in_script(hass, "script.unknown") == []
    assert script.floors_in_script(hass, "script.unknown") == []
    assert script.areas_in_script(hass, "script.unknown") == []
    assert script.blueprint_in_script(hass, "script.unknown") is None
    assert script.devices_in_script(hass, "script.unknown") == []
    assert script.entities_in_script(hass, "script.unknown") == []