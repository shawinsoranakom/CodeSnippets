async def test_empty_aliases(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test that empty aliases are not added to slot lists."""
    floor_1 = floor_registry.async_create("first floor", aliases={" "})

    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, aliases={" "}, floor_id=floor_1.floor_id
    )

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(kitchen_device.id, area_id=area_kitchen.id)

    kitchen_light = entity_registry.async_get_or_create("light", "demo", "1234")
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id,
        device_id=kitchen_device.id,
        name="kitchen light",
        aliases=[er.COMPUTED_NAME, " "],
    )
    hass.states.async_set(
        kitchen_light.entity_id,
        "on",
        attributes={ATTR_FRIENDLY_NAME: kitchen_light.name},
    )

    with patch(
        "homeassistant.components.conversation.default_agent.DefaultAgent._recognize",
        return_value=None,
    ) as mock_recognize_all:
        await conversation.async_converse(
            hass, "turn on kitchen light", None, Context(), None
        )

        assert mock_recognize_all.call_count > 0
        slot_lists = mock_recognize_all.call_args[0][2]

        # Slot lists should only contain non-empty text
        assert slot_lists.keys() == {"area", "name", "floor"}
        areas = slot_lists["area"]
        assert len(areas.values) == 1
        assert areas.values[0].text_in.text == area_kitchen.normalized_name

        names = slot_lists["name"]
        assert len(names.values) == 1
        assert names.values[0].text_in.text == kitchen_light.name

        floors = slot_lists["floor"]
        assert len(floors.values) == 1
        assert floors.values[0].text_in.text == floor_1.name