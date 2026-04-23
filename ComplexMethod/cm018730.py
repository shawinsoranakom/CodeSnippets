async def test_turn_on_off_intent_lock(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test HassTurnOn/Off intent on lock domains."""
    assert await async_setup_component(hass, "intent", {})

    lock = entity_registry.async_get_or_create("lock", "test", "lock_uid")

    hass.states.async_set(lock.entity_id, "locked")
    unlock_calls = async_mock_service(hass, "lock", SERVICE_UNLOCK)
    lock_calls = async_mock_service(hass, "lock", SERVICE_LOCK)

    await intent.async_handle(
        hass, "test", "HassTurnOn", {"name": {"value": lock.entity_id}}
    )

    assert len(lock_calls) == 1
    call = lock_calls[0]
    assert call.domain == "lock"
    assert call.service == SERVICE_LOCK
    assert call.data == {"entity_id": lock.entity_id}

    await intent.async_handle(
        hass, "test", "HassTurnOff", {"name": {"value": lock.entity_id}}
    )

    assert len(unlock_calls) == 1
    call = unlock_calls[0]
    assert call.domain == "lock"
    assert call.service == SERVICE_UNLOCK
    assert call.data == {"entity_id": lock.entity_id}