async def test_async_match_states(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test async_match_state helper."""
    area_kitchen = area_registry.async_get_or_create("kitchen")
    area_kitchen = area_registry.async_update(area_kitchen.id, aliases={"food room"})
    area_bedroom = area_registry.async_get_or_create("bedroom")

    # Kitchen is on the first floor
    floor_1 = floor_registry.async_create("first floor", aliases={"ground floor"})
    area_kitchen = area_registry.async_update(
        area_kitchen.id, floor_id=floor_1.floor_id
    )

    # Bedroom is on the second floor
    floor_2 = floor_registry.async_create("second floor")
    area_bedroom = area_registry.async_update(
        area_bedroom.id, floor_id=floor_2.floor_id
    )

    state1 = State(
        "light.kitchen", "on", attributes={ATTR_FRIENDLY_NAME: "kitchen light"}
    )
    state2 = State(
        "switch.bedroom", "on", attributes={ATTR_FRIENDLY_NAME: "bedroom switch"}
    )

    # Put entities into different areas
    entity_registry.async_get_or_create(
        "light",
        "demo",
        "1234",
        suggested_object_id="kitchen",
        original_name="kitchen light",
    )
    entity_registry.async_update_entity(
        state1.entity_id, area_id=area_kitchen.id, aliases=[er.COMPUTED_NAME]
    )

    entity_registry.async_get_or_create(
        "switch",
        "demo",
        "5678",
        suggested_object_id="bedroom",
        original_name="bedroom switch",
    )
    entity_registry.async_update_entity(
        state2.entity_id,
        area_id=area_bedroom.id,
        device_class=switch.SwitchDeviceClass.OUTLET,
        aliases=[er.COMPUTED_NAME, "kill switch"],
    )

    # Match on name
    assert list(
        intent.async_match_states(hass, name="kitchen light", states=[state1, state2])
    ) == [state1]

    # Test alias
    assert list(
        intent.async_match_states(hass, name="kill switch", states=[state1, state2])
    ) == [state2]

    # Name + area
    assert list(
        intent.async_match_states(
            hass, name="kitchen light", area_name="kitchen", states=[state1, state2]
        )
    ) == [state1]

    # Test area alias
    assert list(
        intent.async_match_states(
            hass, name="kitchen light", area_name="food room", states=[state1, state2]
        )
    ) == [state1]

    # Wrong area
    assert not list(
        intent.async_match_states(
            hass, name="kitchen light", area_name="bedroom", states=[state1, state2]
        )
    )

    # Invalid area
    assert not list(
        intent.async_match_states(
            hass, area_name="invalid area", states=[state1, state2]
        )
    )

    # Domain + area
    assert list(
        intent.async_match_states(
            hass, domains={"switch"}, area_name="bedroom", states=[state1, state2]
        )
    ) == [state2]

    # Device class + area
    assert list(
        intent.async_match_states(
            hass,
            device_classes={switch.SwitchDeviceClass.OUTLET},
            area_name="bedroom",
            states=[state1, state2],
        )
    ) == [state2]

    # Floor
    assert list(
        intent.async_match_states(
            hass, floor_name="first floor", states=[state1, state2]
        )
    ) == [state1]

    assert list(
        intent.async_match_states(
            # Check alias
            hass,
            floor_name="ground floor",
            states=[state1, state2],
        )
    ) == [state1]

    assert list(
        intent.async_match_states(
            hass, floor_name="second floor", states=[state1, state2]
        )
    ) == [state2]

    # Invalid floor
    assert not list(
        intent.async_match_states(
            hass, floor_name="invalid floor", states=[state1, state2]
        )
    )