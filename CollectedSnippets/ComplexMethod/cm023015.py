async def test_duplicated_names_resolved_with_device_area(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test entities deduplication with device ID context."""
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    bedroom_light = entity_registry.async_get_or_create("light", "demo", "5678")

    # Same name and alias
    for light in (kitchen_light, bedroom_light):
        light = entity_registry.async_update_entity(
            light.entity_id,
            name="top light",
            aliases=[er.COMPUTED_NAME, "overhead light"],
        )
        hass.states.async_set(
            light.entity_id,
            "off",
            attributes={ATTR_FRIENDLY_NAME: light.name},
        )
    # Different areas
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        area_id=area_kitchen.id,
    )
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id,
        area_id=area_bedroom.id,
    )

    # Pipeline device in bedroom area
    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    assist_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    assist_device = device_registry.async_update_device(
        assist_device.id,
        area_id=area_bedroom.id,
    )

    # Check name and alias
    for name in ("top light", "overhead light"):
        # Only one light should be turned on
        calls = async_mock_service(hass, "light", "turn_on")
        result = await conversation.async_converse(
            hass, f"turn on {name}", None, Context(), device_id=assist_device.id
        )

        assert len(calls) == 1
        assert calls[0].data["entity_id"][0] == bedroom_light.entity_id

        assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
        assert result.response.intent is not None
        assert result.response.intent.slots.get("name", {}).get("value") == name
        assert result.response.intent.slots.get("name", {}).get("text") == name