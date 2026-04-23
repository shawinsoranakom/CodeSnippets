async def test_lock_service_calls(
    hass: HomeAssistant,
    mock_tedee: MagicMock,
) -> None:
    """Test the tedee lock."""

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {
            ATTR_ENTITY_ID: "lock.lock_1a2b",
        },
        blocking=True,
    )

    assert len(mock_tedee.lock.mock_calls) == 1
    mock_tedee.lock.assert_called_once_with(12345)
    state = hass.states.get("lock.lock_1a2b")
    assert state
    assert state.state == LockState.LOCKING

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {
            ATTR_ENTITY_ID: "lock.lock_1a2b",
        },
        blocking=True,
    )

    assert len(mock_tedee.unlock.mock_calls) == 1
    mock_tedee.unlock.assert_called_once_with(12345)
    state = hass.states.get("lock.lock_1a2b")
    assert state
    assert state.state == LockState.UNLOCKING

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_OPEN,
        {
            ATTR_ENTITY_ID: "lock.lock_1a2b",
        },
        blocking=True,
    )

    assert len(mock_tedee.open.mock_calls) == 1
    mock_tedee.open.assert_called_once_with(12345)
    state = hass.states.get("lock.lock_1a2b")
    assert state
    assert state.state == LockState.UNLOCKING