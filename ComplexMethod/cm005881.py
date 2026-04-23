def test_camel_to_snake_edge_cases(self):
        """Test edge cases for camelCase conversion."""
        # Already snake_case should remain unchanged
        assert util._camel_to_snake("snake_case") == "snake_case"
        assert util._camel_to_snake("already_snake") == "already_snake"

        # Single word should remain unchanged
        assert util._camel_to_snake("simple") == "simple"
        assert util._camel_to_snake("UPPER") == "upper"

        # Multiple consecutive capitals
        assert util._camel_to_snake("XMLHttpRequest") == "xmlhttp_request"
        assert util._camel_to_snake("HTTPSConnection") == "httpsconnection"

        # Numbers
        assert util._camel_to_snake("version2Beta") == "version2_beta"
        assert util._camel_to_snake("test123Value") == "test123_value"