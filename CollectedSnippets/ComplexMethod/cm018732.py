async def test_get_temperature(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test HassClimateGetTemperature intent."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "intent", {})

    climate_1 = MockClimateEntity()
    climate_1._attr_name = "Climate 1"
    climate_1._attr_unique_id = "1234"
    climate_1._attr_current_temperature = 10.0
    entity_registry.async_get_or_create(
        CLIMATE_DOMAIN, "test", "1234", suggested_object_id="climate_1"
    )

    climate_2 = MockClimateEntity()
    climate_2._attr_name = "Climate 2"
    climate_2._attr_unique_id = "5678"
    climate_2._attr_current_temperature = 22.0
    entity_registry.async_get_or_create(
        CLIMATE_DOMAIN, "test", "5678", suggested_object_id="climate_2"
    )

    await create_mock_platform(hass, [climate_1, climate_2])

    # Add climate entities to different areas:
    # climate_1 => living room
    # climate_2 => bedroom
    # nothing in bathroom
    # nothing in office yet
    # nothing in attic yet
    living_room_area = area_registry.async_create(name="Living Room")
    bedroom_area = area_registry.async_create(name="Bedroom")
    office_area = area_registry.async_create(name="Office")
    attic_area = area_registry.async_create(name="Attic")
    bathroom_area = area_registry.async_create(name="Bathroom")

    entity_registry.async_update_entity(
        climate_1.entity_id, area_id=living_room_area.id
    )
    entity_registry.async_update_entity(climate_2.entity_id, area_id=bedroom_area.id)

    # Put areas on different floors:
    # first floor => living room and office
    # 2nd floor => bedroom
    # 3rd floor => attic
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
    bathroom_area = area_registry.async_update(
        bathroom_area.id, floor_id=second_floor.floor_id
    )

    third_floor = floor_registry.async_create("Third floor")
    attic_area = area_registry.async_update(
        attic_area.id, floor_id=third_floor.floor_id
    )

    # Add temperature sensors to each area that should *not* be selected
    for area in (living_room_area, office_area, bedroom_area, attic_area):
        wrong_temperature_entry = entity_registry.async_get_or_create(
            "sensor", "test", f"wrong_temperature_{area.id}"
        )
        hass.states.async_set(
            wrong_temperature_entry.entity_id,
            "10.0",
            {
                ATTR_TEMPERATURE: "Temperature",
                ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
            },
        )
        entity_registry.async_update_entity(
            wrong_temperature_entry.entity_id, area_id=area.id
        )

    # Create temperature sensor and assign them to the office/attic
    office_temperature_id = "sensor.office_temperature"
    attic_temperature_id = "sensor.attic_temperature"
    hass.states.async_set(
        office_temperature_id,
        "15.5",
        {
            ATTR_TEMPERATURE: "Temperature",
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
    )
    office_area = area_registry.async_update(
        office_area.id, temperature_entity_id=office_temperature_id
    )

    hass.states.async_set(
        attic_temperature_id,
        "18.1",
        {
            ATTR_TEMPERATURE: "Temperature",
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        },
    )
    attic_area = area_registry.async_update(
        attic_area.id, temperature_entity_id=attic_temperature_id
    )

    # Multiple climate entities match (error)
    with pytest.raises(intent.MatchFailedError) as error:
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {},
            assistant=conversation.DOMAIN,
        )

    # Exception should contain details of what we tried to match
    assert isinstance(error.value, intent.MatchFailedError)
    assert (
        error.value.result.no_match_reason == intent.MatchFailedReason.MULTIPLE_TARGETS
    )

    # Select by area (office_temperature)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"area": {"value": office_area.name}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == office_temperature_id
    state = response.matched_states[0]
    assert state.state == "15.5"

    # Select by preferred area (attic_temperature)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"preferred_area_id": {"value": attic_area.id}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == attic_temperature_id
    state = response.matched_states[0]
    assert state.state == "18.1"

    # Select by area (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"area": {"value": bedroom_area.name}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = response.matched_states[0]
    assert state.attributes["current_temperature"] == 22.0

    # Select by name (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"name": {"value": "Climate 2"}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = response.matched_states[0]
    assert state.attributes["current_temperature"] == 22.0

    # Check area with no climate entities
    with pytest.raises(intent.MatchFailedError) as error:
        response = await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"area": {"value": bathroom_area.name}},
            assistant=conversation.DOMAIN,
        )

    # Exception should contain details of what we tried to match
    assert isinstance(error.value, intent.MatchFailedError)
    assert error.value.result.no_match_reason == intent.MatchFailedReason.AREA
    constraints = error.value.constraints
    assert constraints.name is None
    assert constraints.area_name == bathroom_area.name
    assert constraints.domains and (set(constraints.domains) == {CLIMATE_DOMAIN})
    assert constraints.device_classes is None

    # Check wrong name
    with pytest.raises(intent.MatchFailedError) as error:
        response = await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"name": {"value": "Does not exist"}},
        )

    assert isinstance(error.value, intent.MatchFailedError)
    assert error.value.result.no_match_reason == intent.MatchFailedReason.NAME
    constraints = error.value.constraints
    assert constraints.name == "Does not exist"
    assert constraints.area_name is None
    assert constraints.domains and (set(constraints.domains) == {CLIMATE_DOMAIN})
    assert constraints.device_classes is None

    # Check wrong name with area
    with pytest.raises(intent.MatchFailedError) as error:
        response = await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"name": {"value": "Climate 1"}, "area": {"value": bedroom_area.name}},
        )

    assert isinstance(error.value, intent.MatchFailedError)
    assert error.value.result.no_match_reason == intent.MatchFailedReason.AREA
    constraints = error.value.constraints
    assert constraints.name == "Climate 1"
    assert constraints.area_name == bedroom_area.name
    assert constraints.domains and (set(constraints.domains) == {CLIMATE_DOMAIN})
    assert constraints.device_classes is None

    # Select by floor (climate_1)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"floor": {"value": first_floor.name}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_1.entity_id
    state = response.matched_states[0]
    assert state.attributes["current_temperature"] == 10.0

    # Select by preferred area (climate_2)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"preferred_area_id": {"value": bedroom_area.id}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id
    state = response.matched_states[0]
    assert state.attributes["current_temperature"] == 22.0

    # Select by preferred floor (climate_1)
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"preferred_floor_id": {"value": first_floor.floor_id}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_1.entity_id
    state = response.matched_states[0]
    assert state.attributes["current_temperature"] == 10.0