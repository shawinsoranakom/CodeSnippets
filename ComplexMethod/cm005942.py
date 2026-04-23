def test_build_embeddings_passes_all_optional_params(self, mock_get_embeddings, component_class, default_kwargs):
        """Test that all optional parameters are forwarded correctly."""
        mock_get_embeddings.return_value = MagicMock()

        component = component_class(**default_kwargs)
        component._user_id = "test-user-id"
        component.api_key = "test-key"
        component.api_base = "https://custom.api.base"
        component.dimensions = 512
        component.chunk_size = 500
        component.request_timeout = 30.0
        component.max_retries = 5
        component.show_progress_bar = True
        component.model_kwargs = {"extra_param": "value"}

        component.build_embeddings()

        call_kwargs = mock_get_embeddings.call_args.kwargs
        assert call_kwargs["api_base"] == "https://custom.api.base"
        assert call_kwargs["dimensions"] == 512
        assert call_kwargs["chunk_size"] == 500
        assert call_kwargs["request_timeout"] == 30.0
        assert call_kwargs["max_retries"] == 5
        assert call_kwargs["show_progress_bar"] is True
        assert call_kwargs["model_kwargs"] == {"extra_param": "value"}