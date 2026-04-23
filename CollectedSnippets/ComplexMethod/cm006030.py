def test_build_embedding_metadata_without_api_key(self, component_class, default_kwargs):
        """Test _build_embedding_metadata with no API key stores model_selection for later use."""
        component = component_class(**default_kwargs)
        model_selection = [
            {"name": "sentence-transformers/all-MiniLM-L6-v2", "provider": "HuggingFace", "metadata": {}}
        ]

        metadata = component._build_embedding_metadata(model_selection, api_key=None)

        assert metadata["embedding_provider"] == "HuggingFace"
        assert metadata["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert metadata["api_key"] is None
        assert metadata["api_key_used"] is False
        # New in this PR: full model_selection is stored alongside the string fields so
        # build_kb_info() can reconstruct the embedding client without hitting the model registry.
        assert "model_selection" in metadata
        assert metadata["model_selection"]["name"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert metadata["model_selection"]["provider"] == "HuggingFace"