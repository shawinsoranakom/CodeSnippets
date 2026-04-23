async def test_extraction_functions_not_setup(hass: HomeAssistant) -> None:
    """Test extraction functions when script is not setup."""
    assert script.scripts_with_area(hass, "area-in-both") == []
    assert script.areas_in_script(hass, "script.test") == []
    assert script.scripts_with_blueprint(hass, "blabla.yaml") == []
    assert script.blueprint_in_script(hass, "script.test") is None
    assert script.scripts_with_device(hass, "device-in-both") == []
    assert script.devices_in_script(hass, "script.test") == []
    assert script.scripts_with_entity(hass, "light.in_both") == []
    assert script.entities_in_script(hass, "script.test") == []
    assert script.scripts_with_floor(hass, "floor-in-both") == []
    assert script.floors_in_script(hass, "script.test") == []
    assert script.scripts_with_label(hass, "label-in-both") == []
    assert script.labels_in_script(hass, "script.test") == []