def test_only_problematic_sequences_removed(self):
        """Test that ONLY PostgreSQL-problematic sequences are removed, nothing else."""
        # Mix of problematic and safe content (using actual control characters)
        mixed_content = {
            "safe_and_unsafe": "Good text\twith tab\x00NULL BYTE\nand newline\x08BACKSPACE",
            "file_path_with_null": "C:\\temp\\file\x00.txt",
            "json_with_controls": '{"text": "data\x01\x0C\x1F"}',
        }

        result = SafeJson(mixed_content)
        result_data = cast(dict[str, Any], result.data)
        assert isinstance(result_data, dict)

        # Verify only problematic characters are removed
        safe_and_unsafe = result_data.get("safe_and_unsafe", "")
        file_path_with_null = result_data.get("file_path_with_null", "")

        assert "Good text" in str(safe_and_unsafe)
        assert "\t" in str(safe_and_unsafe)  # Tab preserved
        assert "\n" in str(safe_and_unsafe)  # Newline preserved
        assert "\x00" not in str(safe_and_unsafe)  # Null removed
        assert "\x08" not in str(safe_and_unsafe)  # Backspace removed

        assert "C:\\temp\\file" in str(file_path_with_null)
        assert ".txt" in str(file_path_with_null)
        assert "\x00" not in str(file_path_with_null)