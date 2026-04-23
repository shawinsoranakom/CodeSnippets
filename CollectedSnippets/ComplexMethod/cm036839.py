async def test_serving_chat_should_set_correct_max_tokens():
    mock_engine = MagicMock(spec=AsyncLLM)
    mock_engine.errored = False
    mock_engine.model_config = MockModelConfig()
    mock_engine.input_processor = MagicMock()
    mock_engine.renderer = _build_renderer(mock_engine.model_config)

    serving_chat = _build_serving_chat(mock_engine)

    req = ChatCompletionRequest(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "what is 1+1?"}],
    )

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 93

    req.max_tokens = 10
    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 10

    # Model author's generation_config.json sets max_tokens (auto, no override)
    # — should act as fallback only, not ceiling
    mock_model_config = MockModelConfig()
    mock_model_config.diff_sampling_param = {"max_tokens": 10}

    # Reinitialize the engine with new settings
    mock_engine = MagicMock(spec=AsyncLLM)
    mock_engine.errored = False
    mock_engine.model_config = mock_model_config
    mock_engine.input_processor = MagicMock()
    mock_engine.renderer = _build_renderer(mock_engine.model_config)

    # Initialize the serving chat
    serving_chat = _build_serving_chat(mock_engine)

    # Test Case 1: No max_tokens specified in request
    req = ChatCompletionRequest(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "what is 1+1?"}],
    )

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 10

    # Test Case 2: Request's max_tokens set higher than generation_config
    # default so request-provided max_tokens takes precedence
    req.max_tokens = 15

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 15

    # Test Case 3: Request's max_tokens set lower than server accepts
    req.max_tokens = 5

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 5

    # User explicitly sets max_tokens via --override-generation-config
    # — should act as a ceiling
    mock_model_config = MockModelConfig()
    mock_model_config.diff_sampling_param = {"max_tokens": 10}
    mock_model_config.override_generation_config = {"max_new_tokens": 10}

    mock_engine = MagicMock(spec=AsyncLLM)
    mock_engine.errored = False
    mock_engine.model_config = mock_model_config
    mock_engine.input_processor = MagicMock()
    mock_engine.renderer = _build_renderer(mock_engine.model_config)

    serving_chat = _build_serving_chat(mock_engine)

    # Test Case 3.1: No max_tokens — uses override as default
    req = ChatCompletionRequest(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "what is 1+1?"}],
    )

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 10

    # Test Case 3.2: Request max_tokens higher — capped by user ceiling from override
    req.max_tokens = 15

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 10

    # Test Case 3.3: Request max_tokens lower — respected
    req.max_tokens = 5

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 5

    # Setting server's max_tokens in the generation_config.json
    # higher than context_window - prompt_tokens
    mock_model_config = MockModelConfig()
    mock_model_config.diff_sampling_param = {"max_tokens": 200}

    # Reinitialize the engine with new settings
    mock_engine = MagicMock(spec=AsyncLLM)
    mock_engine.errored = False
    mock_engine.model_config = mock_model_config
    mock_engine.input_processor = MagicMock()
    mock_engine.renderer = _build_renderer(mock_engine.model_config)

    # Initialize the serving chat
    serving_chat = _build_serving_chat(mock_engine)

    # Test case 1: No max_tokens specified, defaults to context_window
    req = ChatCompletionRequest(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "what is 1+1?"}],
    )

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 93

    # Test Case 2: Request's max_tokens set higher than server accepts
    req.max_tokens = 100

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 93

    # Test Case 3: Request's max_tokens set lower than server accepts
    req.max_tokens = 5

    with suppress(Exception):
        await serving_chat.create_chat_completion(req)

    assert mock_engine.generate.call_args.args[1].max_tokens == 5