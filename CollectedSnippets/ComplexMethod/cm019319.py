async def test_state_reporting(hass: HomeAssistant) -> None:
    """Test the state reporting.

    The group state is unavailable if all group members are unavailable.
    Otherwise, the group state is unknown if at least one group member is unknown or unavailable.
    Otherwise, the group state is jammed if at least one group member is jammed.
    Otherwise, the group state is locking if at least one group member is locking.
    Otherwise, the group state is unlocking if at least one group member is unlocking.
    Otherwise, the group state is unlocked if at least one group member is unlocked.
    Otherwise, the group state is locked.
    """
    await async_setup_component(
        hass,
        LOCK_DOMAIN,
        {
            LOCK_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["lock.test1", "lock.test2"],
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    # Initial state with no group member in the state machine -> unavailable
    assert hass.states.get("lock.lock_group").state == STATE_UNAVAILABLE

    # All group members unavailable -> unavailable
    hass.states.async_set("lock.test1", STATE_UNAVAILABLE)
    hass.states.async_set("lock.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("lock.lock_group").state == STATE_UNAVAILABLE

    # The group state is unknown if all group members are unknown or unavailable.
    for state_1 in (
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    ):
        hass.states.async_set("lock.test1", state_1)
        hass.states.async_set("lock.test2", STATE_UNKNOWN)
        await hass.async_block_till_done()
        assert hass.states.get("lock.lock_group").state == STATE_UNKNOWN

    # At least one member jammed -> group jammed
    for state_1 in (
        LockState.JAMMED,
        LockState.LOCKED,
        LockState.LOCKING,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
        LockState.UNLOCKED,
        LockState.UNLOCKING,
    ):
        hass.states.async_set("lock.test1", state_1)
        hass.states.async_set("lock.test2", LockState.JAMMED)
        await hass.async_block_till_done()
        assert hass.states.get("lock.lock_group").state == LockState.JAMMED

    # At least one member locking -> group unlocking
    for state_1 in (
        LockState.LOCKED,
        LockState.LOCKING,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
        LockState.UNLOCKED,
        LockState.UNLOCKING,
    ):
        hass.states.async_set("lock.test1", state_1)
        hass.states.async_set("lock.test2", LockState.LOCKING)
        await hass.async_block_till_done()
        assert hass.states.get("lock.lock_group").state == LockState.LOCKING

    # At least one member unlocking -> group unlocking
    for state_1 in (
        LockState.LOCKED,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
        LockState.UNLOCKED,
        LockState.UNLOCKING,
    ):
        hass.states.async_set("lock.test1", state_1)
        hass.states.async_set("lock.test2", LockState.UNLOCKING)
        await hass.async_block_till_done()
        assert hass.states.get("lock.lock_group").state == LockState.UNLOCKING

    # At least one member unlocked -> group unlocked
    for state_1 in (
        LockState.LOCKED,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
        LockState.UNLOCKED,
    ):
        hass.states.async_set("lock.test1", state_1)
        hass.states.async_set("lock.test2", LockState.UNLOCKED)
        await hass.async_block_till_done()
        assert hass.states.get("lock.lock_group").state == LockState.UNLOCKED

    # Otherwise -> locked
    hass.states.async_set("lock.test1", LockState.LOCKED)
    hass.states.async_set("lock.test2", LockState.LOCKED)
    await hass.async_block_till_done()
    assert hass.states.get("lock.lock_group").state == LockState.LOCKED

    # All group members removed from the state machine -> unavailable
    hass.states.async_remove("lock.test1")
    hass.states.async_remove("lock.test2")
    await hass.async_block_till_done()
    assert hass.states.get("lock.lock_group").state == STATE_UNAVAILABLE