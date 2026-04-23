def test_append_mode_hidden_for_cloud_storage(self, component_class):
        """Test that append_mode is hidden for AWS and Google Drive storage."""
        component = component_class()

        # Test Local storage - append_mode should be visible
        build_config = {
            "file_name": {"show": False},
            "append_mode": {"show": False},
            "local_format": {"show": False},
        }
        result = component.update_build_config(build_config, [{"name": "Local"}], "storage_location")
        assert result["append_mode"]["show"] is True, "append_mode should be visible for Local storage"
        assert result["file_name"]["show"] is True
        assert result["local_format"]["show"] is True

        # Test AWS storage - append_mode should be hidden
        build_config = {
            "file_name": {"show": False},
            "append_mode": {"show": False},
            "aws_format": {"show": False},
        }
        result = component.update_build_config(build_config, [{"name": "AWS"}], "storage_location")
        assert result["append_mode"]["show"] is False, "append_mode should be hidden for AWS storage"
        assert result["file_name"]["show"] is True
        assert result["aws_format"]["show"] is True

        # Test Google Drive storage - append_mode should be hidden
        build_config = {
            "file_name": {"show": False},
            "append_mode": {"show": False},
            "gdrive_format": {"show": False},
        }
        result = component.update_build_config(build_config, [{"name": "Google Drive"}], "storage_location")
        assert result["append_mode"]["show"] is False, "append_mode should be hidden for Google Drive storage"
        assert result["file_name"]["show"] is True
        assert result["gdrive_format"]["show"] is True