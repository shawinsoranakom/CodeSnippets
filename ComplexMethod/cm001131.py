def test_programming_code_preservation(self):
        """Test that programming code with various escapes is preserved."""
        # Common programming patterns that should be preserved
        code_samples = {
            "python_string": 'print("Hello\\\\nworld")',
            "regex_pattern": "\\\\b[A-Za-z]+\\\\b",  # Word boundary regex
            "json_string": '{"name": "test", "path": "C:\\\\\\\\folder"}',
            "sql_escape": "WHERE name LIKE '%\\\\%%'",
            "javascript": 'var path = "C:\\\\\\\\Users\\\\\\\\file.js";',
        }

        result = SafeJson(code_samples)
        result_data = cast(dict[str, Any], result.data)
        assert isinstance(result_data, dict)

        # Verify programming code is preserved
        python_string = result_data.get("python_string", "")
        regex_pattern = result_data.get("regex_pattern", "")
        json_string = result_data.get("json_string", "")
        sql_escape = result_data.get("sql_escape", "")
        javascript = result_data.get("javascript", "")

        assert "print(" in str(python_string)
        assert "Hello" in str(python_string)
        assert "[A-Za-z]+" in str(regex_pattern)
        assert "name" in str(json_string)
        assert "LIKE" in str(sql_escape)
        assert "var path" in str(javascript)