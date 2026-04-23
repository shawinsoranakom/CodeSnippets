async def test_climate_find_valid_targets() -> None:
    """Test function to return temperature from valid targets."""

    valid_targets = [10, 16, 17, 18, 19, 20]

    assert _find_valid_target_temp(7, valid_targets) == 10
    assert _find_valid_target_temp(10, valid_targets) == 10
    assert _find_valid_target_temp(11, valid_targets) == 16
    assert _find_valid_target_temp(15, valid_targets) == 16
    assert _find_valid_target_temp(16, valid_targets) == 16
    assert _find_valid_target_temp(18.5, valid_targets) == 19
    assert _find_valid_target_temp(20, valid_targets) == 20
    assert _find_valid_target_temp(25, valid_targets) == 20