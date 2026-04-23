def test_build_embeddings_openai(self, mock_get_embeddings, component_class, default_kwargs):
        """Test that build_embeddings delegates to get_embeddings with correct kwargs."""
        mock_instance = MagicMock()
        mock_get_embeddings.return_value = mock_instance

        component = component_class(**default_kwargs)
        component._user_id = "test-user-id"
        component.api_key = "test-key"
        component.chunk_size = 1000
        component.max_retries = 3
        component.show_progress_bar = False
        component.api_base = None
        component.dimensions = None
        component.request_timeout = None
        component.model_kwargs = None

        result = component.build_embeddings()

        # Verify get_embeddings was called with correct parameters
        mock_get_embeddings.assert_called_once()
        call_kwargs = mock_get_embeddings.call_args.kwargs
        assert call_kwargs["api_key"] == "test-key"
        assert call_kwargs["chunk_size"] == 1000
        assert call_kwargs["max_retries"] == 3
        assert call_kwargs["show_progress_bar"] is False
        assert call_kwargs["model"][0]["name"] == "text-embedding-3-small"
        assert call_kwargs["model"][0]["provider"] == "OpenAI"

        # Result should be whatever get_embeddings returns
        assert result == mock_instance