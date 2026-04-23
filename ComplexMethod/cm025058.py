async def test_check_valid_float() -> None:
    """Test extra significant checker works."""
    assert significant_change.check_valid_float("1")
    assert significant_change.check_valid_float("1.0")
    assert significant_change.check_valid_float(1)
    assert significant_change.check_valid_float(1.0)
    assert not significant_change.check_valid_float("")
    assert not significant_change.check_valid_float("invalid")
    assert not significant_change.check_valid_float("1.1.1")