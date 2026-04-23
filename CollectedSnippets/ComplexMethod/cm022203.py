async def test_lock_states(hass: HomeAssistant, mock_lock_entity: MockLock) -> None:
    """Test lock entity states."""

    assert mock_lock_entity.state is None

    mock_lock_entity._attr_is_locking = True
    assert mock_lock_entity.is_locking
    assert mock_lock_entity.state == LockState.LOCKING

    mock_lock_entity._attr_is_locked = True
    mock_lock_entity._attr_is_locking = False
    assert mock_lock_entity.is_locked
    assert mock_lock_entity.state == LockState.LOCKED

    mock_lock_entity._attr_is_unlocking = True
    assert mock_lock_entity.is_unlocking
    assert mock_lock_entity.state == LockState.UNLOCKING

    mock_lock_entity._attr_is_locked = False
    mock_lock_entity._attr_is_unlocking = False
    assert not mock_lock_entity.is_locked
    assert mock_lock_entity.state == LockState.UNLOCKED

    mock_lock_entity._attr_is_jammed = True
    assert mock_lock_entity.is_jammed
    assert mock_lock_entity.state == LockState.JAMMED
    assert not mock_lock_entity.is_locked

    mock_lock_entity._attr_is_jammed = False
    mock_lock_entity._attr_is_opening = True
    assert mock_lock_entity.is_opening
    assert mock_lock_entity.state == LockState.OPENING
    assert mock_lock_entity.is_opening

    mock_lock_entity._attr_is_opening = False
    mock_lock_entity._attr_is_open = True
    assert not mock_lock_entity.is_opening
    assert mock_lock_entity.state == LockState.OPEN
    assert not mock_lock_entity.is_opening
    assert mock_lock_entity.is_open