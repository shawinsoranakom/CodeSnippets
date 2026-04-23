async def test_extraction_functions_unavailable_script(hass: HomeAssistant) -> None:
    """Test extraction functions for an unknown automation."""
    entity_id = "script.test1"
    assert await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: {"test1": {}}},
    )
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    assert script.scripts_with_area(hass, "area-in-both") == []
    assert script.areas_in_script(hass, entity_id) == []
    assert script.scripts_with_blueprint(hass, "blabla.yaml") == []
    assert script.blueprint_in_script(hass, entity_id) is None
    assert script.scripts_with_device(hass, "device-in-both") == []
    assert script.devices_in_script(hass, entity_id) == []
    assert script.scripts_with_entity(hass, "light.in_both") == []
    assert script.entities_in_script(hass, entity_id) == []
    assert script.scripts_with_floor(hass, "floor-in-both") == []
    assert script.floors_in_script(hass, entity_id) == []
    assert script.scripts_with_label(hass, "label-in-both") == []
    assert script.labels_in_script(hass, entity_id) == []