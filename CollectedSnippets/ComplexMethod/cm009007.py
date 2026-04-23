def test_configurable() -> None:
    """Test configurable chat model behavior without default parameters.

    Verifies that a configurable chat model initialized without default parameters:
    - Has access to all standard runnable methods (`invoke`, `stream`, etc.)
    - Blocks access to non-configurable methods until configuration is provided
    - Supports declarative operations (`bind_tools`) without mutating original model
    - Can chain declarative operations and configuration to access full functionality
    - Properly resolves to the configured model type when parameters are provided

    Example:
    ```python
    # This creates a configurable model without specifying which model
    model = init_chat_model()

    # This will FAIL - no model specified yet
    model.get_num_tokens("hello")  # AttributeError!

    # This works - provides model at runtime
    response = model.invoke("Hello", config={"configurable": {"model": "gpt-4o"}})
    ```
    """
    model = init_chat_model()

    for method in (
        "invoke",
        "ainvoke",
        "batch",
        "abatch",
        "stream",
        "astream",
        "batch_as_completed",
        "abatch_as_completed",
    ):
        assert hasattr(model, method)

    # Doesn't have access non-configurable, non-declarative methods until a config is
    # provided.
    for method in ("get_num_tokens", "get_num_tokens_from_messages"):
        with pytest.raises(AttributeError):
            getattr(model, method)

    # Can call declarative methods even without a default model.
    model_with_tools = model.bind_tools(
        [{"name": "foo", "description": "foo", "parameters": {}}],
    )

    # Check that original model wasn't mutated by declarative operation.
    assert model._queued_declarative_operations == []

    # Can iteratively call declarative methods.
    model_with_config = model_with_tools.with_config(
        RunnableConfig(tags=["foo"]),
        configurable={"model": "gpt-4o"},
    )
    assert model_with_config.model_name == "gpt-4o"  # type: ignore[attr-defined]

    for method in ("get_num_tokens", "get_num_tokens_from_messages"):
        assert hasattr(model_with_config, method)

    expected: dict[str, Any] = {
        "name": None,
        "bound": {
            "name": None,
            "disable_streaming": False,
            "disabled_params": None,
            "model_name": "gpt-4o",
            "temperature": None,
            "model_kwargs": {},
            "openai_api_key": SecretStr("foo"),
            "openai_api_base": None,
            "openai_organization": None,
            "openai_proxy": None,
            "output_version": None,
            "request_timeout": None,
            "max_retries": None,
            "presence_penalty": None,
            "reasoning": None,
            "reasoning_effort": None,
            "verbosity": None,
            "frequency_penalty": None,
            "context_management": None,
            "include": None,
            "seed": None,
            "service_tier": None,
            "logprobs": None,
            "top_logprobs": None,
            "logit_bias": None,
            "streaming": False,
            "n": None,
            "top_p": None,
            "truncation": None,
            "max_tokens": None,
            "tiktoken_model_name": None,
            "default_headers": None,
            "default_query": None,
            "stop": None,
            "store": None,
            "extra_body": None,
            "include_response_headers": False,
            "stream_usage": True,
            "use_previous_response_id": False,
            "use_responses_api": None,
        },
        "kwargs": {
            "tools": [
                {
                    "type": "function",
                    "function": {"name": "foo", "description": "foo", "parameters": {}},
                },
            ],
        },
        "config": {
            "callbacks": None,
            "configurable": {},
            "metadata": {"model": "gpt-4o"},
            "recursion_limit": 25,
            "tags": ["foo"],
        },
        "config_factories": [],
        "custom_input_type": None,
        "custom_output_type": None,
    }
    assert model_with_config.model_dump() == expected