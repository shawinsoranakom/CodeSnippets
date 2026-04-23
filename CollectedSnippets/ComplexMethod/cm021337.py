async def test_set_temperature(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test HassClimateSetTemperature intent."""
    assert await async_setup_component(hass, "homeassistant", {})
    await climate_intent.async_setup_intents(hass)

    climate_1 = MockClimateEntity()
    climate_1._attr_name = "Climate 1"
    climate_1._attr_unique_id = "1234"
    climate_1._attr_current_temperature = 10.0
    climate_1._attr_target_temperature = 10.0
    entity_registry.async_get_or_create(
        DOMAIN, "test", "1234", suggested_object_id="climate_1"
    )

    climate_2 = MockClimateEntity()
    climate_2._attr_name = "Climate 2"
    climate_2._attr_unique_id = "5678"
    climate_2._attr_current_temperature = 22.0
    climate_2._attr_target_temperature = 22.0
    entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", suggested_object_id="climate_2"
    )

    await create_mock_platform(hass, [climate_1, climate_2])

    # Add climate entities to different areas:
    # climate_1 => living room
    # climate_2 => bedroom
    # nothing in office
    living_room_area = area_registry.async_create(name="Living Room")
    bedroom_area = area_registry.async_create(name="Bedroom")
    office_area = area_registry.async_create(name="Office")

    entity_registry.async_update_entity(
        climate_1.entity_id, area_id=living_room_area.id
    )
    entity_registry.async_update_entity(climate_2.entity_id, area_id=bedroom_area.id)

    # Put areas on different floors:
    # first floor => living room and office
    # upstairs => bedroom
    floor_registry = fr.async_get(hass)
    first_floor = floor_registry.async_create("First floor")
    living_room_area = area_registry.async_update(
        living_room_area.id, floor_id=first_floor.floor_id
    )
    office_area = area_registry.async_update(
        office_area.id, floor_id=first_floor.floor_id
    )

    second_floor = floor_registry.async_create("Second floor")
    bedroom_area = area_registry.async_update(
        bedroom_area.id, floor_id=second_floor.floor_id
    )

    # Cannot target multiple climate devices
    with pytest.raises(intent.MatchFailedError) as err:
        await intent.async_handle(
            hass,
            "test",
            climate_intent.INTENT_SET_TEMPERATURE,
            {"temperature": {"value": 20}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == intent.MatchFailedReason.MULTIPLE_TARGETS

    # Select by area explicitly (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        climate_intent.INTENT_SET_TEMPERATURE,
        {"area": {"value": bedroom_area.name}, "temperature": {"value": 20.1}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = hass.states.get(climate_2.entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 20.1

    # Select by area implicitly (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        climate_intent.INTENT_SET_TEMPERATURE,
        {
            "preferred_area_id": {"value": bedroom_area.id},
            "temperature": {"value": 20.2},
        },
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.matched_states
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = hass.states.get(climate_2.entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 20.2

    # Select by floor explicitly (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        climate_intent.INTENT_SET_TEMPERATURE,
        {"floor": {"value": second_floor.name}, "temperature": {"value": 20.3}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.matched_states
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = hass.states.get(climate_2.entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 20.3

    # Select by floor implicitly (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        climate_intent.INTENT_SET_TEMPERATURE,
        {
            "preferred_floor_id": {"value": second_floor.floor_id},
            "temperature": {"value": 20.4},
        },
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert response.matched_states
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = hass.states.get(climate_2.entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 20.4

    # Select by name (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        climate_intent.INTENT_SET_TEMPERATURE,
        {"name": {"value": "Climate 2"}, "temperature": {"value": 20.5}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = hass.states.get(climate_2.entity_id)
    assert state.attributes[ATTR_TEMPERATURE] == 20.5

    # Check area with no climate entities (explicit)
    with pytest.raises(intent.MatchFailedError) as error:
        response = await intent.async_handle(
            hass,
            "test",
            climate_intent.INTENT_SET_TEMPERATURE,
            {"area": {"value": office_area.name}, "temperature": {"value": 20.6}},
            assistant=conversation.DOMAIN,
        )

    # Exception should contain details of what we tried to match
    assert isinstance(error.value, intent.MatchFailedError)
    assert error.value.result.no_match_reason == intent.MatchFailedReason.AREA
    constraints = error.value.constraints
    assert constraints.name is None
    assert constraints.area_name == office_area.name
    assert constraints.domains and (set(constraints.domains) == {DOMAIN})
    assert constraints.device_classes is None

    # Implicit area with no climate entities will fail with multiple targets
    with pytest.raises(intent.MatchFailedError) as err:
        await intent.async_handle(
            hass,
            "test",
            climate_intent.INTENT_SET_TEMPERATURE,
            {
                "preferred_area_id": {"value": office_area.id},
                "temperature": {"value": 20.7},
            },
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == intent.MatchFailedReason.MULTIPLE_TARGETS