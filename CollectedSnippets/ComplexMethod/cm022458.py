async def test_lock_unlock_lock(hass: HomeAssistant) -> None:
    """Test LockUnlock trait locking support for lock domain."""
    assert helpers.get_google_type(lock.DOMAIN, None) is not None
    assert trait.LockUnlockTrait.supported(
        lock.DOMAIN, LockEntityFeature.OPEN, None, None
    )
    assert trait.LockUnlockTrait.might_2fa(lock.DOMAIN, LockEntityFeature.OPEN, None)

    trt = trait.LockUnlockTrait(
        hass, State("lock.front_door", lock.LockState.LOCKED), PIN_CONFIG
    )

    assert trt.sync_attributes() == {}

    assert trt.query_attributes() == {"isLocked": True}

    assert trt.can_execute(trait.COMMAND_LOCK_UNLOCK, {"lock": True})

    calls = async_mock_service(hass, lock.DOMAIN, lock.SERVICE_LOCK)

    await trt.execute(trait.COMMAND_LOCK_UNLOCK, PIN_DATA, {"lock": True}, {})

    assert len(calls) == 1
    assert calls[0].data == {ATTR_ENTITY_ID: "lock.front_door"}