def test_leap_year_datetime(self):
        """Test datetime on leap day"""
        original_dt = datetime.datetime(2024, 2, 29, 14, 30, 15, 500000)
        result = datetime_format(original_dt)

        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 15
        assert result.microsecond == 0