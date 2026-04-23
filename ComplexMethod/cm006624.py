def test_get_local_path_with_s3_json_file(self, component_class):
        """Test _get_local_path downloads S3 JSON files to temp."""
        component = component_class()
        s3_path = "flow_456/config.json"
        component.set_attributes({"llm": MagicMock(), "path": s3_path})

        json_content = b'{"key": "value", "number": 42}'

        # Mock S3 storage and read - real temp file creation
        with (
            patch("lfx.components.langchain_utilities.json_agent.get_settings_service") as mock_get_settings,
            patch(
                "lfx.components.langchain_utilities.json_agent.read_file_bytes", new_callable=AsyncMock
            ) as mock_read_bytes,
        ):
            mock_settings = MagicMock()
            mock_settings.settings.storage_type = "s3"
            mock_get_settings.return_value = mock_settings
            mock_read_bytes.return_value = json_content

            # Real temp file creation
            local_path = component._get_local_path()

            # Verify real temp file was created
            assert isinstance(local_path, Path)
            import tempfile

            temp_dir = tempfile.gettempdir()
            assert str(local_path).startswith(temp_dir)
            assert str(local_path).endswith(".json")
            assert local_path.exists()
            assert local_path.read_bytes() == json_content
            assert hasattr(component, "_temp_file_path")

            # Cleanup
            component._cleanup_temp_file()
            assert not local_path.exists()