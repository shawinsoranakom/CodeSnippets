def test_remove_microseconds(self):
        """Test that microseconds are removed from datetime object"""
        original_dt = datetime.datetime(2024, 1, 1, 12, 30, 45, 123456)
        result = datetime_format(original_dt)

        # Verify microseconds are 0
        assert result.microsecond == 0
        # Verify other components remain the same
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45