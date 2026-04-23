def test_add_serialized_and_buffer_writer_integration(self):
        """Integration test: add_serialized followed by buffer_writer.

        This simulates the real processor chain where add_serialized adds
        bytes and buffer_writer uses it directly.
        """
        event_dict = {
            "timestamp": 1625097600.123,
            "event": "Integration test message",
            "module": "test_module",
        }

        with patch.object(log_buffer, "enabled", return_value=True):
            # Step 1: add_serialized adds the bytes field
            after_add = add_serialized(None, "debug", event_dict)

            # Verify serialized field was added and is bytes
            assert "serialized" in after_add
            assert isinstance(after_add["serialized"], bytes)

            # Step 2: buffer_writer should use the serialized field directly
            with patch.object(log_buffer, "write") as mock_write:
                result = buffer_writer(None, "debug", after_add)

            # Should have called write
            mock_write.assert_called_once()
            # Verify result is returned
            assert result == after_add

            # Should have written the decoded serialized field
            call_args = mock_write.call_args[0]
            written_json = call_args[0]
            parsed_data = json.loads(written_json)

            # Should contain the subset created by add_serialized
            assert parsed_data["timestamp"] == 1625097600.123
            assert parsed_data["message"] == "Integration test message"
            assert parsed_data["level"] == "DEBUG"
            assert parsed_data["module"] == "test_module"