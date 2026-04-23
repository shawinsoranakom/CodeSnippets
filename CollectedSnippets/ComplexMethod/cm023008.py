async def test_turn_floor_lights_on_off(
    hass: HomeAssistant,
    init_components,
    entity_registry: er.EntityRegistry,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test that we can turn lights on/off for an entire floor."""
    floor_ground = floor_registry.async_create("ground", aliases={"downstairs"})
    floor_upstairs = floor_registry.async_create("upstairs")

    # Kitchen and living room are on the ground floor
    area_kitchen = area_registry.async_get_or_create("kitchen_id")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, name="kitchen", floor_id=floor_ground.floor_id
    )

    area_living_room = area_registry.async_get_or_create("living_room_id")
    area_living_room = area_registry.async_update(
        area_living_room.id, name="living_room", floor_id=floor_ground.floor_id
    )

    # Bedroom is upstairs
    area_bedroom = area_registry.async_get_or_create("bedroom_id")
    area_bedroom = area_registry.async_update(
        area_bedroom.id, name="bedroom", floor_id=floor_upstairs.floor_id
    )

    # One light per area
    kitchen_light = entity_registry.async_get_or_create(
        "light", "demo", "kitchen_light"
    )
    kitchen_light = entity_registry.async_update_entity(
        kitchen_light.entity_id, area_id=area_kitchen.id
    )
    hass.states.async_set(kitchen_light.entity_id, "off")

    living_room_light = entity_registry.async_get_or_create(
        "light", "demo", "living_room_light"
    )
    living_room_light = entity_registry.async_update_entity(
        living_room_light.entity_id, area_id=area_living_room.id
    )
    hass.states.async_set(living_room_light.entity_id, "off")

    bedroom_light = entity_registry.async_get_or_create(
        "light", "demo", "bedroom_light"
    )
    bedroom_light = entity_registry.async_update_entity(
        bedroom_light.entity_id, area_id=area_bedroom.id
    )
    hass.states.async_set(bedroom_light.entity_id, "off")

    # Target by floor
    on_calls = async_mock_service(hass, light.DOMAIN, light.SERVICE_TURN_ON)
    result = await conversation.async_converse(
        hass, "turn on all lights downstairs", None, Context(), None
    )

    assert len(on_calls) == 2
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert {s.entity_id for s in result.response.matched_states} == {
        kitchen_light.entity_id,
        living_room_light.entity_id,
    }

    on_calls.clear()
    result = await conversation.async_converse(
        hass, "upstairs lights on", None, Context(), None
    )

    assert len(on_calls) == 1
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert {s.entity_id for s in result.response.matched_states} == {
        bedroom_light.entity_id
    }

    off_calls = async_mock_service(hass, light.DOMAIN, light.SERVICE_TURN_OFF)
    result = await conversation.async_converse(
        hass, "turn upstairs lights off", None, Context(), None
    )

    assert len(off_calls) == 1
    assert result.response.response_type == intent.IntentResponseType.ACTION_DONE
    assert {s.entity_id for s in result.response.matched_states} == {
        bedroom_light.entity_id
    }