def test_datetime_with_max_microseconds(self):
        """Test datetime with maximum microseconds value"""
        original_dt = datetime.datetime(2024, 1, 1, 12, 30, 45, 999999)
        result = datetime_format(original_dt)

        # Microseconds should be removed
        assert result.microsecond == 0
        # Other components should remain
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45