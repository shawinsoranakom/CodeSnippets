async def test_async_match_targets(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    floor_registry: fr.FloorRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Tests for async_match_targets function."""
    # Needed for exposure
    assert await async_setup_component(hass, "homeassistant", {})

    # House layout
    # Floor 1 (ground):
    #   - Kitchen
    #     - Outlet
    #   - Bathroom
    #     - Light
    # Floor 2 (upstairs)
    #   - Bedroom
    #     - Switch
    #   - Bathroom
    #     - Light
    # Floor 3 (also upstairs)
    #   - Bedroom
    #     - Switch
    #   - Bathroom
    #     - Light

    # Floor 1
    floor_1 = floor_registry.async_create("first floor", aliases={"ground"})
    area_kitchen = area_registry.async_get_or_create("kitchen")
    area_kitchen = area_registry.async_update(
        area_kitchen.id, floor_id=floor_1.floor_id
    )
    area_bathroom_1 = area_registry.async_get_or_create("first floor bathroom")
    area_bathroom_1 = area_registry.async_update(
        area_bathroom_1.id, aliases={"bathroom"}, floor_id=floor_1.floor_id
    )

    kitchen_outlet = entity_registry.async_get_or_create(
        "switch", "test", "kitchen_outlet"
    )
    kitchen_outlet = entity_registry.async_update_entity(
        kitchen_outlet.entity_id,
        name="kitchen outlet",
        aliases=[er.COMPUTED_NAME],
        device_class=switch.SwitchDeviceClass.OUTLET,
        area_id=area_kitchen.id,
    )
    state_kitchen_outlet = State(kitchen_outlet.entity_id, "on")

    bathroom_light_1 = entity_registry.async_get_or_create(
        "light", "test", "bathroom_light_1"
    )
    bathroom_light_1 = entity_registry.async_update_entity(
        bathroom_light_1.entity_id,
        name="bathroom light",
        aliases=[er.COMPUTED_NAME, "overhead light"],
        area_id=area_bathroom_1.id,
    )
    state_bathroom_light_1 = State(bathroom_light_1.entity_id, "off")

    # Floor 2
    floor_2 = floor_registry.async_create("second floor", aliases={"upstairs"})
    area_bedroom_2 = area_registry.async_get_or_create("second floor bedroom")
    area_bedroom_2 = area_registry.async_update(
        area_bedroom_2.id, floor_id=floor_2.floor_id
    )
    area_bathroom_2 = area_registry.async_get_or_create("second floor bathroom")
    area_bathroom_2 = area_registry.async_update(
        area_bathroom_2.id, aliases={"bathroom"}, floor_id=floor_2.floor_id
    )

    bedroom_switch_2 = entity_registry.async_get_or_create(
        "switch", "test", "bedroom_switch_2"
    )
    bedroom_switch_2 = entity_registry.async_update_entity(
        bedroom_switch_2.entity_id,
        name="second floor bedroom switch",
        aliases=[er.COMPUTED_NAME],
        area_id=area_bedroom_2.id,
    )
    state_bedroom_switch_2 = State(
        bedroom_switch_2.entity_id,
        "off",
    )

    bathroom_light_2 = entity_registry.async_get_or_create(
        "light", "test", "bathroom_light_2"
    )
    bathroom_light_2 = entity_registry.async_update_entity(
        bathroom_light_2.entity_id,
        aliases=[er.COMPUTED_NAME, "bathroom light", "overhead light"],
        area_id=area_bathroom_2.id,
        supported_features=light.LightEntityFeature.EFFECT,
    )
    state_bathroom_light_2 = State(bathroom_light_2.entity_id, "off")

    # Floor 3
    floor_3 = floor_registry.async_create("third floor", aliases={"upstairs"})
    area_bedroom_3 = area_registry.async_get_or_create("third floor bedroom")
    area_bedroom_3 = area_registry.async_update(
        area_bedroom_3.id, floor_id=floor_3.floor_id
    )
    area_bathroom_3 = area_registry.async_get_or_create("third floor bathroom")
    area_bathroom_3 = area_registry.async_update(
        area_bathroom_3.id, aliases={"bathroom"}, floor_id=floor_3.floor_id
    )

    bedroom_switch_3 = entity_registry.async_get_or_create(
        "switch", "test", "bedroom_switch_3"
    )
    bedroom_switch_3 = entity_registry.async_update_entity(
        bedroom_switch_3.entity_id,
        name="third floor bedroom switch",
        aliases=[er.COMPUTED_NAME],
        area_id=area_bedroom_3.id,
    )
    state_bedroom_switch_3 = State(
        bedroom_switch_3.entity_id,
        "off",
        attributes={ATTR_DEVICE_CLASS: switch.SwitchDeviceClass.OUTLET},
    )

    bathroom_light_3 = entity_registry.async_get_or_create(
        "light", "test", "bathroom_light_3"
    )
    bathroom_light_3 = entity_registry.async_update_entity(
        bathroom_light_3.entity_id,
        name="overhead light",
        aliases=[er.COMPUTED_NAME, "bathroom light"],
        area_id=area_bathroom_3.id,
    )
    state_bathroom_light_3 = State(
        bathroom_light_3.entity_id,
        "on",
        attributes={
            ATTR_FRIENDLY_NAME: "bathroom light",
            ATTR_SUPPORTED_FEATURES: light.LightEntityFeature.EFFECT,
        },
    )

    # -----
    bathroom_light_states = [
        state_bathroom_light_1,
        state_bathroom_light_2,
        state_bathroom_light_3,
    ]
    states = [
        *bathroom_light_states,
        state_kitchen_outlet,
        state_bedroom_switch_2,
        state_bedroom_switch_3,
    ]

    # Not a unique name
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(name="bathroom light"),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == intent.MatchFailedReason.DUPLICATE_NAME
    assert result.no_match_name == "bathroom light"

    # Works with duplicate names allowed
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            name="bathroom light", allow_duplicate_names=True
        ),
        states=states,
    )
    assert result.is_match
    assert {s.entity_id for s in result.states} == {
        s.entity_id for s in bathroom_light_states
    }

    # Also works when name is not a constraint
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(domains={"light"}),
        states=states,
    )
    assert result.is_match
    assert {s.entity_id for s in result.states} == {
        s.entity_id for s in bathroom_light_states
    }

    # We can disambiguate by preferred floor (from context)
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(name="bathroom light"),
        intent.MatchTargetsPreferences(floor_id=floor_3.floor_id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_3.entity_id

    # Also disambiguate by preferred area (from context)
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(name="bathroom light"),
        intent.MatchTargetsPreferences(area_id=area_bathroom_2.id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_2.entity_id

    # Disambiguate by floor name, if unique
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(name="bathroom light", floor_name="ground"),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Doesn't work if floor name/alias is not unique
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(name="bathroom light", floor_name="upstairs"),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == intent.MatchFailedReason.DUPLICATE_NAME

    # Disambiguate by area name, if unique
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            name="bathroom light", area_name="first floor bathroom"
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Doesn't work if area name/alias is not unique
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(name="bathroom light", area_name="bathroom"),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == intent.MatchFailedReason.DUPLICATE_NAME

    # Does work if floor/area name combo is unique
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            name="bathroom light", area_name="bathroom", floor_name="ground"
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Doesn't work if area is not part of the floor
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            name="bathroom light",
            area_name="second floor bathroom",
            floor_name="ground",
        ),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == intent.MatchFailedReason.AREA

    # Check state constraint (only third floor bathroom light is on)
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(domains={"light"}, states={"on"}),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_3.entity_id

    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            domains={"light"}, states={"on"}, floor_name="ground"
        ),
        states=states,
    )
    assert not result.is_match

    # Check assistant constraint (exposure)
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(assistant="test"),
        states=states,
    )
    assert not result.is_match

    async_expose_entity(hass, "test", bathroom_light_1.entity_id, True)
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(assistant="test"),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Check device class constraint
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            domains={"switch"}, device_classes={switch.SwitchDeviceClass.OUTLET}
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 2
    assert {s.entity_id for s in result.states} == {
        kitchen_outlet.entity_id,
        bedroom_switch_3.entity_id,
    }

    # Check features constraint (second and third floor bathroom lights have effects)
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(
            domains={"light"}, features=light.LightEntityFeature.EFFECT
        ),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 2
    assert {s.entity_id for s in result.states} == {
        bathroom_light_2.entity_id,
        bathroom_light_3.entity_id,
    }

    # Check single target constraint
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(domains={"light"}, single_target=True),
        states=states,
    )
    assert not result.is_match
    assert result.no_match_reason == intent.MatchFailedReason.MULTIPLE_TARGETS

    # Only one light on the ground floor
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(domains={"light"}, single_target=True),
        preferences=intent.MatchTargetsPreferences(floor_id=floor_1.floor_id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bathroom_light_1.entity_id

    # Only one switch in bedroom
    result = intent.async_match_targets(
        hass,
        intent.MatchTargetsConstraints(domains={"switch"}, single_target=True),
        preferences=intent.MatchTargetsPreferences(area_id=area_bedroom_2.id),
        states=states,
    )
    assert result.is_match
    assert len(result.states) == 1
    assert result.states[0].entity_id == bedroom_switch_2.entity_id