async def test_get_state_intent(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test HassGetState intent.

    This tests name, area, domain, device class, and state constraints.
    """
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "intent", {})

    bedroom = area_registry.async_get_or_create("bedroom")
    kitchen = area_registry.async_get_or_create("kitchen")
    office = area_registry.async_get_or_create("office")

    # 1 light in bedroom (off)
    # 1 light in kitchen (on)
    # 1 sensor in kitchen (50)
    # 2 binary sensors in the office (problem, moisture, on)
    bedroom_light = entity_registry.async_get_or_create(
        "light", "demo", "1", original_name="bedroom light"
    )
    entity_registry.async_update_entity(bedroom_light.entity_id, area_id=bedroom.id)

    kitchen_sensor = entity_registry.async_get_or_create(
        "sensor", "demo", "2", original_name="kitchen sensor"
    )
    entity_registry.async_update_entity(kitchen_sensor.entity_id, area_id=kitchen.id)

    kitchen_light = entity_registry.async_get_or_create(
        "light", "demo", "3", original_name="kitchen light"
    )
    entity_registry.async_update_entity(kitchen_light.entity_id, area_id=kitchen.id)

    kitchen_sensor = entity_registry.async_get_or_create(
        "sensor", "demo", "4", original_name="kitchen sensor"
    )
    entity_registry.async_update_entity(kitchen_sensor.entity_id, area_id=kitchen.id)

    problem_sensor = entity_registry.async_get_or_create(
        "binary_sensor", "demo", "5", original_name="problem sensor"
    )
    entity_registry.async_update_entity(problem_sensor.entity_id, area_id=office.id)

    moisture_sensor = entity_registry.async_get_or_create(
        "binary_sensor", "demo", "6", original_name="moisture sensor"
    )
    entity_registry.async_update_entity(moisture_sensor.entity_id, area_id=office.id)

    hass.states.async_set(
        bedroom_light.entity_id, "off", attributes={ATTR_FRIENDLY_NAME: "bedroom light"}
    )
    hass.states.async_set(
        kitchen_light.entity_id, "on", attributes={ATTR_FRIENDLY_NAME: "kitchen light"}
    )
    hass.states.async_set(
        kitchen_sensor.entity_id,
        "50.0",
        attributes={ATTR_FRIENDLY_NAME: "kitchen sensor"},
    )
    hass.states.async_set(
        problem_sensor.entity_id,
        "on",
        attributes={ATTR_FRIENDLY_NAME: "problem sensor", ATTR_DEVICE_CLASS: "problem"},
    )
    hass.states.async_set(
        moisture_sensor.entity_id,
        "on",
        attributes={
            ATTR_FRIENDLY_NAME: "moisture sensor",
            ATTR_DEVICE_CLASS: "moisture",
        },
    )

    # ---
    # is bedroom light off?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {"name": {"value": "bedroom light"}, "state": {"value": "off"}},
    )

    # yes
    assert result.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert result.matched_states and (
        result.matched_states[0].entity_id == bedroom_light.entity_id
    )
    assert not result.unmatched_states

    # ---
    # is light in kitchen off?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "kitchen"},
            "domain": {"value": "light"},
            "state": {"value": "off"},
        },
    )

    # no, it's on
    assert result.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert not result.matched_states
    assert result.unmatched_states and (
        result.unmatched_states[0].entity_id == kitchen_light.entity_id
    )

    # ---
    # what is the value of the kitchen sensor?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "name": {"value": "kitchen sensor"},
        },
    )

    assert result.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert result.matched_states and (
        result.matched_states[0].entity_id == kitchen_sensor.entity_id
    )
    assert not result.unmatched_states

    # ---
    # is there a problem in the office?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "office"},
            "device_class": {"value": "problem"},
            "state": {"value": "on"},
        },
    )

    # yes
    assert result.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert result.matched_states and (
        result.matched_states[0].entity_id == problem_sensor.entity_id
    )
    assert not result.unmatched_states

    # ---
    # is there a problem or a moisture sensor in the office?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "office"},
            "device_class": {"value": ["problem", "moisture"]},
        },
    )

    # yes, 2 of them
    assert result.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(result.matched_states) == 2 and {
        state.entity_id for state in result.matched_states
    } == {problem_sensor.entity_id, moisture_sensor.entity_id}
    assert not result.unmatched_states

    # ---
    # are there any binary sensors in the kitchen?
    result = await intent.async_handle(
        hass,
        "test",
        "HassGetState",
        {
            "area": {"value": "kitchen"},
            "domain": {"value": "binary_sensor"},
        },
    )

    # no
    assert result.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert not result.matched_states and not result.unmatched_states

    # Test unknown area failure
    with pytest.raises(intent.MatchFailedError):
        await intent.async_handle(
            hass,
            "test",
            "HassGetState",
            {
                "area": {"value": "does-not-exist"},
                "domain": {"value": "light"},
            },
        )