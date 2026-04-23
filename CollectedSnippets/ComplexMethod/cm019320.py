async def test_service_calls_openable(hass: HomeAssistant) -> None:
    """Test service calls with open support."""
    await async_setup_component(
        hass,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: [
                {"platform": "kitchen_sink"},
                {
                    "platform": DOMAIN,
                    "entities": [
                        "lock.openable_lock",
                        "lock.another_openable_lock",
                    ],
                },
            ]
        },
    )
    await hass.async_block_till_done()

    group_state = hass.states.get("lock.lock_group")
    assert group_state.state == LockState.UNLOCKED
    assert hass.states.get("lock.openable_lock").state == LockState.LOCKED
    assert hass.states.get("lock.another_openable_lock").state == LockState.UNLOCKED

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_OPEN,
        {ATTR_ENTITY_ID: "lock.lock_group"},
        blocking=True,
    )
    assert hass.states.get("lock.openable_lock").state == LockState.OPEN
    assert hass.states.get("lock.another_openable_lock").state == LockState.OPEN

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {ATTR_ENTITY_ID: "lock.lock_group"},
        blocking=True,
    )
    assert hass.states.get("lock.openable_lock").state == LockState.LOCKED
    assert hass.states.get("lock.another_openable_lock").state == LockState.LOCKED

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: "lock.lock_group"},
        blocking=True,
    )
    assert hass.states.get("lock.openable_lock").state == LockState.UNLOCKED
    assert hass.states.get("lock.another_openable_lock").state == LockState.UNLOCKED