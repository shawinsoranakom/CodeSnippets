def test_invalid_escape_error_prevention(self):
        """Test that SafeJson prevents 'Invalid \\escape' errors that occurred in upsert_execution_output."""
        # This reproduces the exact scenario that was causing the error:
        # POST /upsert_execution_output failed: Invalid \escape: line 1 column 36404 (char 36403)

        # Create data with various problematic escape sequences that could cause JSON parsing errors
        problematic_output_data = {
            "web_content": "Article text\x00with null\x01and control\x08chars\x0C\x1F\x7F",
            "file_path": "C:\\Users\\test\\file\x00.txt",
            "json_like_string": '{"text": "data\x00\x08\x1F"}',
            "escaped_sequences": "Text with \\u0000 and \\u0008 sequences",
            "mixed_content": "Normal text\tproperly\nformatted\rwith\x00invalid\x08chars\x1Fmixed",
            "large_text": "A" * 35000
            + "\x00\x08\x1F"
            + "B" * 5000,  # Large text like in the error
        }

        # This should not raise any JSON parsing errors
        result = SafeJson(problematic_output_data)
        assert isinstance(result, Json)

        # Verify the result is a valid Json object that can be safely stored in PostgreSQL
        result_data = cast(dict[str, Any], result.data)
        assert isinstance(result_data, dict)

        # Verify problematic characters are removed but safe content preserved
        web_content = result_data.get("web_content", "")
        file_path = result_data.get("file_path", "")
        large_text = result_data.get("large_text", "")

        # Check that control characters are removed
        assert "\x00" not in str(web_content)
        assert "\x01" not in str(web_content)
        assert "\x08" not in str(web_content)
        assert "\x0C" not in str(web_content)
        assert "\x1F" not in str(web_content)
        assert "\x7F" not in str(web_content)

        # Check that legitimate content is preserved
        assert "Article text" in str(web_content)
        assert "with null" in str(web_content)
        assert "and control" in str(web_content)
        assert "chars" in str(web_content)

        # Check file path handling
        assert "C:\\Users\\test\\file" in str(file_path)
        assert ".txt" in str(file_path)
        assert "\x00" not in str(file_path)

        # Check large text handling (the scenario from the error at char 36403)
        assert len(str(large_text)) > 35000  # Content preserved
        assert "A" * 1000 in str(large_text)  # A's preserved
        assert "B" * 1000 in str(large_text)  # B's preserved
        assert "\x00" not in str(large_text)  # Control chars removed
        assert "\x08" not in str(large_text)
        assert "\x1F" not in str(large_text)

        # Most importantly: ensure the result can be JSON-serialized without errors
        # This would have failed with the old approach
        import json

        json_string = json.dumps(result.data)  # Should not raise "Invalid \escape"
        assert len(json_string) > 0

        # And can be parsed back
        parsed_back = json.loads(json_string)
        assert isinstance(parsed_back, dict)