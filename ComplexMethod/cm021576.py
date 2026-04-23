async def test_extraction_functions_unavailable_automation(hass: HomeAssistant) -> None:
    """Test extraction functions for an unknown automation."""
    entity_id = "automation.test1"
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: [
                {
                    "alias": "test1",
                }
            ]
        },
    )
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    assert automation.automations_with_area(hass, "area-in-both") == []
    assert automation.areas_in_automation(hass, entity_id) == []
    assert automation.automations_with_blueprint(hass, "blabla.yaml") == []
    assert automation.blueprint_in_automation(hass, entity_id) is None
    assert automation.automations_with_device(hass, "device-in-both") == []
    assert automation.devices_in_automation(hass, entity_id) == []
    assert automation.automations_with_entity(hass, "light.in_both") == []
    assert automation.entities_in_automation(hass, entity_id) == []
    assert automation.automations_with_floor(hass, "floor-in-both") == []
    assert automation.floors_in_automation(hass, entity_id) == []
    assert automation.automations_with_label(hass, "label-in-both") == []
    assert automation.labels_in_automation(hass, entity_id) == []