def test_parametrized_datetimes(self, year, month, day, hour, minute, second, microsecond):
        """Test multiple datetime scenarios using parametrization"""
        original_dt = datetime.datetime(year, month, day, hour, minute, second, microsecond)
        result = datetime_format(original_dt)

        # Verify microseconds are removed
        assert result.microsecond == 0

        # Verify other components remain the same
        assert result.year == year
        assert result.month == month
        assert result.day == day
        assert result.hour == hour
        assert result.minute == minute
        assert result.second == second