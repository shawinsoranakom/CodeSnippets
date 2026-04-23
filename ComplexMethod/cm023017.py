async def test_satellite_area_context(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that including a satellite will target a specific area."""
    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    turn_off_calls = async_mock_service(hass, "light", "turn_off")

    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(area_kitchen.id, name="kitchen")
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(area_bedroom.id, name="bedroom")

    # Create 2 lights in each area
    area_lights = defaultdict(list)
    all_lights = []
    for area in (area_kitchen, area_bedroom):
        for i in range(2):
            light_entity = entity_registry.async_get_or_create(
                "light", "demo", f"{area.name}-light-{i}"
            )
            light_entity = entity_registry.async_update_entity(
                light_entity.entity_id, area_id=area.id
            )
            hass.states.async_set(
                light_entity.entity_id,
                "off",
                attributes={ATTR_FRIENDLY_NAME: f"{area.name} light {i}"},
            )
            area_lights[area.id].append(light_entity)
            all_lights.append(light_entity)

    # Create voice satellites in each area
    entry = MockConfigEntry()
    entry.add_to_hass(hass)

    kitchen_satellite = entity_registry.async_get_or_create(
        "assist_satellite", "demo", "kitchen"
    )
    entity_registry.async_update_entity(
        kitchen_satellite.entity_id, area_id=area_kitchen.id
    )

    bedroom_satellite = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-satellite-bedroom")},
    )
    device_registry.async_update_device(bedroom_satellite.id, area_id=area_bedroom.id)

    # Turn on lights in the area of a device
    result = await conversation.async_converse(
        hass,
        "turn on the lights",
        None,
        Context(),
        None,
        satellite_id=kitchen_satellite.entity_id,
    )
    await hass.async_block_till_done()
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert result.response.intent.slots["area"]["value"] == area_kitchen.id
    assert result.response.intent.slots["area"]["text"] == area_kitchen.normalized_name

    # Verify only kitchen lights were targeted
    assert {s.entity_id for s in result.response.matched_states} == {
        e.entity_id for e in area_lights[area_kitchen.id]
    }
    assert {c.data["entity_id"][0] for c in turn_on_calls} == {
        e.entity_id for e in area_lights[area_kitchen.id]
    }
    turn_on_calls.clear()

    # Ensure we can still target other areas by name
    result = await conversation.async_converse(
        hass,
        "turn on lights in the bedroom",
        None,
        Context(),
        None,
        satellite_id=kitchen_satellite.entity_id,
    )
    await hass.async_block_till_done()
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert result.response.intent.slots["area"]["value"] == area_bedroom.id
    assert result.response.intent.slots["area"]["text"] == area_bedroom.normalized_name

    # Verify only bedroom lights were targeted
    assert {s.entity_id for s in result.response.matched_states} == {
        e.entity_id for e in area_lights[area_bedroom.id]
    }
    assert {c.data["entity_id"][0] for c in turn_on_calls} == {
        e.entity_id for e in area_lights[area_bedroom.id]
    }
    turn_on_calls.clear()

    # Turn off all lights in the area of the other device
    result = await conversation.async_converse(
        hass,
        "turn lights off",
        None,
        Context(),
        None,
        device_id=bedroom_satellite.id,
    )
    await hass.async_block_till_done()
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert result.response.intent is not None
    assert result.response.intent.slots["area"]["value"] == area_bedroom.id
    assert result.response.intent.slots["area"]["text"] == area_bedroom.normalized_name

    # Verify only bedroom lights were targeted
    assert {s.entity_id for s in result.response.matched_states} == {
        e.entity_id for e in area_lights[area_bedroom.id]
    }
    assert {c.data["entity_id"][0] for c in turn_off_calls} == {
        e.entity_id for e in area_lights[area_bedroom.id]
    }
    turn_off_calls.clear()

    # Turn on/off all lights also works
    for command in ("on", "off"):
        result = await conversation.async_converse(
            hass, f"turn {command} all lights", None, Context(), None
        )
        await hass.async_block_till_done()
        assert result.response.response_type == intent.IntentResponseType.ACTION_DONE

        # All lights should have been targeted
        assert {s.entity_id for s in result.response.matched_states} == {
            e.entity_id for e in all_lights
        }