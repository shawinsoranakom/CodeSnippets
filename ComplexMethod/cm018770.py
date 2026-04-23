async def test_intent_script_targets(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(hass, "test", "service")

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "Targets": {
                    "description": "Intent to control a test service.",
                    "action": {
                        "service": "test.service",
                        "data_template": {
                            "targets": "{{ targets if targets is defined }}",
                        },
                    },
                    "speech": {
                        "text": "{{ targets.entities[0] if targets is defined }}"
                    },
                }
            }
        },
    )

    floor_1 = floor_registry.async_create("first floor")
    kitchen = area_registry.async_get_or_create("kitchen")
    area_registry.async_update(kitchen.id, floor_id=floor_1.floor_id)
    bathroom = area_registry.async_get_or_create("bathroom")
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "kitchen",
        suggested_object_id="kitchen",
        original_name="overhead light",
    )
    entity_registry.async_update_entity("light.kitchen", area_id=kitchen.id)
    hass.states.async_set(
        "light.kitchen", "off", attributes={ATTR_FRIENDLY_NAME: "overhead light"}
    )
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "bathroom",
        suggested_object_id="bathroom",
        original_name="overhead light",
    )
    entity_registry.async_update_entity("light.bathroom", area_id=bathroom.id)
    hass.states.async_set(
        "light.bathroom", "off", attributes={ATTR_FRIENDLY_NAME: "overhead light"}
    )

    response = await intent.async_handle(
        hass,
        "test",
        "Targets",
        {
            "name": {"value": "overhead light"},
            "domain": {"value": "light"},
            "preferred_area_id": {"value": "kitchen"},
        },
    )
    assert len(calls) == 1
    assert calls[0].data["targets"] == {"entities": ["light.kitchen"]}
    assert response.speech["plain"]["speech"] == "light.kitchen"
    calls.clear()

    response = await intent.async_handle(
        hass,
        "test",
        "Targets",
        {
            "area": {"value": "kitchen"},
            "floor": {"value": "first floor"},
        },
    )
    assert len(calls) == 1
    assert calls[0].data["targets"] == {
        "entities": ["light.kitchen"],
        "areas": ["kitchen"],
        "floors": ["first_floor"],
    }
    calls.clear()

    response = await intent.async_handle(
        hass,
        "test",
        "Targets",
        {"device_class": {"value": "door"}},
    )
    assert len(calls) == 1
    assert calls[0].data["targets"] == ""
    calls.clear()