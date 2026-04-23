def test_parse_time_expression() -> None:
    """Test parse_time_expression."""
    assert list(range(60)) == dt_util.parse_time_expression("*", 0, 59)
    assert list(range(60)) == dt_util.parse_time_expression(None, 0, 59)

    assert list(range(0, 60, 5)) == dt_util.parse_time_expression("/5", 0, 59)

    assert dt_util.parse_time_expression("/4", 5, 20) == [8, 12, 16, 20]
    assert dt_util.parse_time_expression("/10", 10, 30) == [10, 20, 30]
    assert dt_util.parse_time_expression("/3", 4, 29) == [6, 9, 12, 15, 18, 21, 24, 27]

    assert dt_util.parse_time_expression([2, 1, 3], 0, 59) == [1, 2, 3]

    assert list(range(24)) == dt_util.parse_time_expression("*", 0, 23)

    assert dt_util.parse_time_expression(42, 0, 59) == [42]
    assert dt_util.parse_time_expression("42", 0, 59) == [42]

    with pytest.raises(ValueError):
        dt_util.parse_time_expression(61, 0, 60)