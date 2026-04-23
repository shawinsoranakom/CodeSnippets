async def test_locks(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    surepetcare,
    mock_config_entry_setup: MockConfigEntry,
) -> None:
    """Test the generation of unique ids."""
    state_entity_ids = hass.states.async_entity_ids()

    for entity_id, unique_id in EXPECTED_ENTITY_IDS.items():
        surepetcare.reset_mock()

        assert entity_id in state_entity_ids
        state = hass.states.get(entity_id)
        assert state
        assert state.state == "unlocked"
        entity = entity_registry.async_get(entity_id)
        assert entity.unique_id == unique_id

        await hass.services.async_call(
            "lock", "unlock", {"entity_id": entity_id}, blocking=True
        )
        state = hass.states.get(entity_id)
        assert state.state == "unlocked"
        # already unlocked
        assert surepetcare.unlock.call_count == 0

        await hass.services.async_call(
            "lock", "lock", {"entity_id": entity_id}, blocking=True
        )
        state = hass.states.get(entity_id)
        assert state.state == "locked"
        if "locked_in" in entity_id:
            assert surepetcare.lock_in.call_count == 1
        elif "locked_out" in entity_id:
            assert surepetcare.lock_out.call_count == 1
        elif "locked_all" in entity_id:
            assert surepetcare.lock.call_count == 1

        # lock again should not trigger another request
        await hass.services.async_call(
            "lock", "lock", {"entity_id": entity_id}, blocking=True
        )
        state = hass.states.get(entity_id)
        assert state.state == "locked"
        if "locked_in" in entity_id:
            assert surepetcare.lock_in.call_count == 1
        elif "locked_out" in entity_id:
            assert surepetcare.lock_out.call_count == 1
        elif "locked_all" in entity_id:
            assert surepetcare.lock.call_count == 1

        await hass.services.async_call(
            "lock", "unlock", {"entity_id": entity_id}, blocking=True
        )
        state = hass.states.get(entity_id)
        assert state.state == "unlocked"
        assert surepetcare.unlock.call_count == 1