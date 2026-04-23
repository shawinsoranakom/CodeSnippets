def test_fallback_models_structure(self, mock_api_key):
        """Test that fallback models have the correct structure."""
        discovery = GroqModelDiscovery(api_key=mock_api_key)
        fallback = discovery._get_fallback_models()

        assert isinstance(fallback, dict)
        assert len(fallback) == 2

        for metadata in fallback.values():
            assert "name" in metadata
            assert "provider" in metadata
            assert "tool_calling" in metadata
            assert "preview" in metadata
            assert metadata["tool_calling"] is True