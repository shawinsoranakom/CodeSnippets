async def test_not_exposed(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test HassClimateGetTemperature intent when entities aren't exposed."""
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

    # Add climate entities to same area
    living_room_area = area_registry.async_create(name="Living Room")
    bedroom_area = area_registry.async_create(name="Bedroom")
    entity_registry.async_update_entity(
        climate_1.entity_id, area_id=living_room_area.id
    )
    entity_registry.async_update_entity(
        climate_2.entity_id, area_id=living_room_area.id
    )

    # Should fail with empty name
    with pytest.raises(intent.InvalidSlotInfo):
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"name": {"value": ""}},
            assistant=conversation.DOMAIN,
        )

    # Should fail with empty area
    with pytest.raises(intent.InvalidSlotInfo):
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"area": {"value": ""}},
            assistant=conversation.DOMAIN,
        )

    # Expose second, hide first
    async_expose_entity(hass, conversation.DOMAIN, climate_1.entity_id, False)
    async_expose_entity(hass, conversation.DOMAIN, climate_2.entity_id, True)

    # Second climate entity is exposed
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id

    # Using the area should work
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"area": {"value": living_room_area.name}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id

    # Using the name of the exposed entity should work
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {"name": {"value": climate_2.name}},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_2.entity_id

    # Using the name of the *unexposed* entity should fail
    with pytest.raises(intent.MatchFailedError) as err:
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"name": {"value": climate_1.name}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == intent.MatchFailedReason.ASSISTANT

    # Expose first, hide second
    async_expose_entity(hass, conversation.DOMAIN, climate_1.entity_id, True)
    async_expose_entity(hass, conversation.DOMAIN, climate_2.entity_id, False)

    # Second climate entity is exposed
    response = await intent.async_handle(
        hass,
        "test",
        intent.INTENT_GET_TEMPERATURE,
        {},
        assistant=conversation.DOMAIN,
    )
    assert response.response_type == intent.IntentResponseType.QUERY_ANSWER
    assert len(response.matched_states) == 1
    assert response.matched_states[0].entity_id == climate_1.entity_id

    # Wrong area name
    with pytest.raises(intent.MatchFailedError) as err:
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"area": {"value": bedroom_area.name}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == intent.MatchFailedReason.AREA

    # Neither are exposed
    async_expose_entity(hass, conversation.DOMAIN, climate_1.entity_id, False)
    async_expose_entity(hass, conversation.DOMAIN, climate_2.entity_id, False)

    with pytest.raises(intent.MatchFailedError) as err:
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == intent.MatchFailedReason.ASSISTANT

    # Should fail with area
    with pytest.raises(intent.MatchFailedError) as err:
        await intent.async_handle(
            hass,
            "test",
            intent.INTENT_GET_TEMPERATURE,
            {"area": {"value": living_room_area.name}},
            assistant=conversation.DOMAIN,
        )
    assert err.value.result.no_match_reason == intent.MatchFailedReason.ASSISTANT

    # Should fail with both names
    for name in (climate_1.name, climate_2.name):
        with pytest.raises(intent.MatchFailedError) as err:
            await intent.async_handle(
                hass,
                "test",
                intent.INTENT_GET_TEMPERATURE,
                {"name": {"value": name}},
                assistant=conversation.DOMAIN,
            )
        assert err.value.result.no_match_reason == intent.MatchFailedReason.ASSISTANT