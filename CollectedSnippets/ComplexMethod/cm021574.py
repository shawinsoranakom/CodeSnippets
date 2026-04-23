async def test_extraction_functions_not_setup(hass: HomeAssistant) -> None:
    """Test extraction functions when automation is not setup."""
    assert automation.automations_with_area(hass, "area-in-both") == []
    assert automation.areas_in_automation(hass, "automation.test") == []
    assert automation.automations_with_blueprint(hass, "blabla.yaml") == []
    assert automation.blueprint_in_automation(hass, "automation.test") is None
    assert automation.automations_with_device(hass, "device-in-both") == []
    assert automation.devices_in_automation(hass, "automation.test") == []
    assert automation.automations_with_entity(hass, "light.in_both") == []
    assert automation.entities_in_automation(hass, "automation.test") == []
    assert automation.automations_with_floor(hass, "floor-in-both") == []
    assert automation.floors_in_automation(hass, "automation.test") == []
    assert automation.automations_with_label(hass, "label-in-both") == []
    assert automation.labels_in_automation(hass, "automation.test") == []