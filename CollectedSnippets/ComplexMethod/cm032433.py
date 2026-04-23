def test_datetime_with_only_date_components(self):
        """Test datetime with only date components (time defaults to 00:00:00)"""
        original_dt = datetime.datetime(2024, 1, 1)
        result = datetime_format(original_dt)

        # Should have zero time components and zero microseconds
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0