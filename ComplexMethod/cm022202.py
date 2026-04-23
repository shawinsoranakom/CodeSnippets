async def test_lock_default(hass: HomeAssistant, mock_lock_entity: MockLock) -> None:
    """Test lock entity with defaults."""

    assert mock_lock_entity.code_format is None
    assert mock_lock_entity.state is None
    assert mock_lock_entity.is_jammed is None
    assert mock_lock_entity.is_locked is None
    assert mock_lock_entity.is_locking is None
    assert mock_lock_entity.is_unlocking is None
    assert mock_lock_entity.is_opening is None
    assert mock_lock_entity.is_open is None