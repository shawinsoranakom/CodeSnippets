def test_logprobs_params_passed_to_client() -> None:
    """Test that logprobs parameters are correctly passed to the Ollama client."""
    response = [
        {
            "model": MODEL_NAME,
            "created_at": "2025-01-01T00:00:00.000000000Z",
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
            "done_reason": "stop",
        }
    ]

    with patch("langchain_ollama.chat_models.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.return_value = response

        # Case 1: logprobs=True, top_logprobs=5 in init
        llm = ChatOllama(model=MODEL_NAME, logprobs=True, top_logprobs=5)
        llm.invoke([HumanMessage("Hello")])

        call_kwargs = mock_client.chat.call_args[1]
        assert call_kwargs["logprobs"] is True
        assert call_kwargs["top_logprobs"] == 5

        # Case 2: override via invoke kwargs
        llm = ChatOllama(model=MODEL_NAME)
        llm.invoke([HumanMessage("Hello")], logprobs=True, top_logprobs=3)

        call_kwargs = mock_client.chat.call_args[1]
        assert call_kwargs["logprobs"] is True
        assert call_kwargs["top_logprobs"] == 3

        # Case 3: auto-enabled logprobs propagates to client
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            llm = ChatOllama(model=MODEL_NAME, top_logprobs=3)
        llm.invoke([HumanMessage("Hello")])

        call_kwargs = mock_client.chat.call_args[1]
        assert call_kwargs["logprobs"] is True
        assert call_kwargs["top_logprobs"] == 3

        # Case 4: defaults are None when not set
        llm = ChatOllama(model=MODEL_NAME)
        llm.invoke([HumanMessage("Hello")])

        call_kwargs = mock_client.chat.call_args[1]
        assert call_kwargs["logprobs"] is None
        assert call_kwargs["top_logprobs"] is None