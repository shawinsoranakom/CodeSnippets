def test_parse_timestamp_parses_iso_format(self):
        """Test parsing ISO format timestamp."""
        timestamp_str = "2024-01-01T12:34:56Z"

        result = RunFlowBaseComponent._parse_timestamp(timestamp_str)

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 34
        assert result.second == 56
        assert result.microsecond == 0