def test_none_parameters_excluded_from_options() -> None:
    """Test that None parameters are excluded from the options dict sent to Ollama."""
    response = [
        {
            "model": "test-model",
            "created_at": "2025-01-01T00:00:00.000000000Z",
            "done": True,
            "done_reason": "stop",
            "message": {"role": "assistant", "content": "Hello!"},
        }
    ]

    with patch("langchain_ollama.chat_models.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = response

        # Create ChatOllama with only num_ctx set
        llm = ChatOllama(model="test-model", num_ctx=4096)
        llm.invoke([HumanMessage("Hello")])

        # Verify that chat was called
        assert mock_client.chat.called

        # Get the options dict that was passed to chat
        call_kwargs = mock_client.chat.call_args[1]
        options = call_kwargs.get("options", {})

        # Only num_ctx should be in options, not None parameters
        assert "num_ctx" in options
        assert options["num_ctx"] == 4096

        # These parameters should NOT be in options since they were None
        assert "mirostat" not in options
        assert "mirostat_eta" not in options
        assert "mirostat_tau" not in options
        assert "tfs_z" not in options