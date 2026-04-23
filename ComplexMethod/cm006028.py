def test_advanced_mode_disabled_in_cloud(self, monkeypatch):
        """Test that advanced_mode and all Docling fields are disabled when ASTRA_CLOUD_DISABLE_COMPONENT is set."""
        # Set the environment variable to simulate cloud environment
        monkeypatch.setenv("ASTRA_CLOUD_DISABLE_COMPONENT", "true")

        component = FileComponent()
        build_config = {
            "advanced_mode": {"show": True, "value": False},
            "pipeline": {"show": False},
            "ocr_engine": {"show": False},
            "doc_key": {"show": False},
            "md_image_placeholder": {"show": False},
            "md_page_break_placeholder": {"show": False},
            "path": {"file_path": ["document.pdf"]},
        }

        result = component.update_build_config(build_config, ["document.pdf"], "path")

        # In cloud, advanced_mode should be hidden regardless of file type
        assert result["advanced_mode"]["show"] is False, "advanced_mode should be hidden in cloud"
        assert result["advanced_mode"]["value"] is False, "advanced_mode value should be False in cloud"
        # All related fields should be hidden
        assert result["pipeline"]["show"] is False
        assert result["ocr_engine"]["show"] is False
        assert result["ocr_engine"]["value"] == "None"
        assert result["doc_key"]["show"] is False
        assert result["md_image_placeholder"]["show"] is False
        assert result["md_page_break_placeholder"]["show"] is False