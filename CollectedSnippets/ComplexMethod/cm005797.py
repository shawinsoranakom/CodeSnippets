def test_buffer_writer_uses_serialized_field_only(self):
        """Test buffer_writer uses only the serialized field, ignoring others."""
        import orjson

        # The serialized field is what gets written to the buffer
        serialized_data = {"key": "value", "message": "Test"}
        event_dict = {
            "event": "Test",
            "serialized": orjson.dumps(serialized_data),
            "another_bytes": b"some bytes",  # Another bytes field (ignored)
            "bytearray_field": bytearray(b"bytearray data"),  # bytearray (ignored)
            "normal_field": "normal string",  # normal field (ignored)
        }

        with (
            patch.object(log_buffer, "enabled", return_value=True),
            patch.object(log_buffer, "write") as mock_write,
        ):
            # Should not crash and should only use the serialized field
            result = buffer_writer(None, "info", event_dict)
            mock_write.assert_called_once()

            # Verify result is returned unchanged
            assert result == event_dict

            # Verify only the serialized field contents were written
            call_args = mock_write.call_args[0]
            written_json = call_args[0]
            parsed_data = json.loads(written_json)

            # Should only contain what was in serialized field
            assert parsed_data == serialized_data
            assert "key" in parsed_data
            assert "message" in parsed_data
            # Other fields from event_dict should NOT be in buffer
            assert "another_bytes" not in parsed_data
            assert "bytearray_field" not in parsed_data
            assert "normal_field" not in parsed_data