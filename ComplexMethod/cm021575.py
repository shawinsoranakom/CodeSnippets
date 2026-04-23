async def test_extraction_functions_unknown_automation(hass: HomeAssistant) -> None:
    """Test extraction functions for an unknown automation."""
    assert await async_setup_component(hass, DOMAIN, {})
    assert automation.areas_in_automation(hass, "automation.unknown") == []
    assert automation.blueprint_in_automation(hass, "automation.unknown") is None
    assert automation.devices_in_automation(hass, "automation.unknown") == []
    assert automation.entities_in_automation(hass, "automation.unknown") == []
    assert automation.floors_in_automation(hass, "automation.unknown") == []
    assert automation.labels_in_automation(hass, "automation.unknown") == []