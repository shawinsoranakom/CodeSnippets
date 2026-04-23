async def test_clean_area(hass: HomeAssistant) -> None:
    """Test HassVacuumCleanArea intent."""
    await vacuum_intent.async_setup_intents(hass)

    area_reg = ar.async_get(hass)
    kitchen = area_reg.async_create("Kitchen")

    vacuum_1 = f"{DOMAIN}.vacuum_1"
    vacuum_2 = f"{DOMAIN}.vacuum_2"
    for entity_id in (vacuum_1, vacuum_2):
        hass.states.async_set(
            entity_id,
            STATE_IDLE,
            {ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.CLEAN_AREA},
        )
    calls = async_mock_service(hass, DOMAIN, SERVICE_CLEAN_AREA)

    # Without name: all vacuums receive the service call
    response = await intent.async_handle(
        hass,
        "test",
        vacuum_intent.INTENT_VACUUM_CLEAN_AREA,
        {"area": {"value": "Kitchen"}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(calls) == 1
    assert set(calls[0].data["entity_id"]) == {vacuum_1, vacuum_2}
    assert calls[0].data["cleaning_area_id"] == [kitchen.id]

    assert len(response.success_results) == 3
    assert response.success_results[0].type == intent.IntentResponseTargetType.AREA
    assert response.success_results[0].id == kitchen.id
    assert all(
        t.type == intent.IntentResponseTargetType.ENTITY
        for t in response.success_results[1:]
    )
    assert {t.id for t in response.success_results[1:]} == {vacuum_1, vacuum_2}

    # With name: only the named vacuum receives the call
    calls.clear()
    response = await intent.async_handle(
        hass,
        "test",
        vacuum_intent.INTENT_VACUUM_CLEAN_AREA,
        {"name": {"value": "vacuum 1"}, "area": {"value": "Kitchen"}},
    )
    await hass.async_block_till_done()

    assert response.response_type == intent.IntentResponseType.ACTION_DONE
    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": [vacuum_1],
        "cleaning_area_id": [kitchen.id],
    }