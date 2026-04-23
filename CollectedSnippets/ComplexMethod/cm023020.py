async def test_duplicate_names_different_areas(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test preferred area when multiple devices have the same name (or alias) in different areas."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")

    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id, area_id=area_kitchen.id
    )
    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id, area_id=area_bedroom.id
    )

    # Same name and alias
    for light in (kitchen_light, bedroom_light):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="test light",
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )

    # Add a satellite in the kitchen and bedroom
    kitchen_entry = MockConfigEntry()
    kitchen_entry.add_to_hass(hass)
    device_kitchen = device_registry.async_get_or_create(
        config_entry_id=kitchen_entry.entry_id,
        connections=set(),
        identifiers={("demo", "device-kitchen")},
    )
    device_registry.async_update_device(device_kitchen.id, area_id=area_kitchen.id)

    bedroom_entry = MockConfigEntry()
    bedroom_entry.add_to_hass(hass)
    device_bedroom = device_registry.async_get_or_create(
        config_entry_id=bedroom_entry.entry_id,
        connections=set(),
        identifiers={("demo", "device-bedroom")},
    )
    device_registry.async_update_device(device_bedroom.id, area_id=area_bedroom.id)

    # Check name and alias
    async_mock_service(hass, "light", "turn_on")
    for name in ("test light", "overhead light"):
        # Should fail without a preferred area
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None
        )
        assert result.response.response_type == intent.IntentResponseType.ERROR

        # Target kitchen light by using kitchen device
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None, device_id=device_kitchen.id
        )
        assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
        assert result.response.matched_states[0].entity_id == kitchen_light.entity_id

        # Target bedroom light by using bedroom device
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), None, device_id=device_bedroom.id
        )
        assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
        assert result.response.matched_states[0].entity_id == bedroom_light.entity_id