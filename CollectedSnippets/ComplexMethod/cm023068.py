def test_time_category() -> None:
    """Test the time category calculation logic."""
    for hour in range(6):
        assert time_category(hour) == "night", hour
    for hour in range(7, 12):
        assert time_category(hour) == "morning", hour
    for hour in range(13, 18):
        assert time_category(hour) == "afternoon", hour
    for hour in range(19, 22):
        assert time_category(hour) == "evening", hour