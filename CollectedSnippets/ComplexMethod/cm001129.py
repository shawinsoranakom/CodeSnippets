def test_control_character_sanitization(self):
        """Test that PostgreSQL-incompatible control characters are sanitized by SafeJson."""
        # Test data with problematic control characters that would cause PostgreSQL errors
        problematic_data = {
            "null_byte": "data with \x00 null",
            "bell_char": "data with \x07 bell",
            "form_feed": "data with \x0C feed",
            "escape_char": "data with \x1B escape",
            "delete_char": "data with \x7F delete",
        }

        # SafeJson should successfully process data with control characters
        result = SafeJson(problematic_data)
        assert isinstance(result, Json)

        # Verify that dangerous control characters are actually removed
        result_data = result.data
        assert "\x00" not in str(result_data)  # null byte removed
        assert "\x07" not in str(result_data)  # bell removed
        assert "\x0C" not in str(result_data)  # form feed removed
        assert "\x1B" not in str(result_data)  # escape removed
        assert "\x7F" not in str(result_data)  # delete removed

        # Test that safe whitespace characters are preserved
        safe_data = {
            "with_tab": "text with \t tab",
            "with_newline": "text with \n newline",
            "with_carriage_return": "text with \r carriage return",
            "normal_text": "completely normal text",
        }

        safe_result = SafeJson(safe_data)
        assert isinstance(safe_result, Json)

        # Verify safe characters are preserved
        safe_result_data = cast(dict[str, Any], safe_result.data)
        assert isinstance(safe_result_data, dict)
        with_tab = safe_result_data.get("with_tab", "")
        with_newline = safe_result_data.get("with_newline", "")
        with_carriage_return = safe_result_data.get("with_carriage_return", "")
        assert "\t" in str(with_tab)  # tab preserved
        assert "\n" in str(with_newline)  # newline preserved
        assert "\r" in str(with_carriage_return)