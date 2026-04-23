def test_configurable_with_default() -> None:
    """Test configurable chat model behavior with default parameters.

    Verifies that a configurable chat model initialized with default parameters:
    - Has access to all standard runnable methods (`invoke`, `stream`, etc.)
    - Provides immediate access to non-configurable methods (e.g. `get_num_tokens`)
    - Supports model switching through runtime configuration using `config_prefix`
    - Maintains proper model identity and attributes when reconfigured
    - Can be used in chains with different model providers via configuration

    Example:
    ```python
    # This creates a configurable model with default parameters (model)
    model = init_chat_model("gpt-4o", configurable_fields="any", config_prefix="bar")

    # This works immediately - uses default gpt-4o
    tokens = model.get_num_tokens("hello")

    # This also works - switches to Claude at runtime
    response = model.invoke(
        "Hello", config={"configurable": {"my_model_model": "claude-3-sonnet-20240229"}}
    )
    ```
    """
    model = init_chat_model("gpt-4o", configurable_fields="any", config_prefix="bar")
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

    # Does have access non-configurable, non-declarative methods since default params
    # are provided.
    for method in ("get_num_tokens", "get_num_tokens_from_messages", "dict"):
        assert hasattr(model, method)

    assert model.model_name == "gpt-4o"

    model_with_tools = model.bind_tools(
        [{"name": "foo", "description": "foo", "parameters": {}}],
    )

    model_with_config = model_with_tools.with_config(
        RunnableConfig(tags=["foo"]),
        configurable={"bar_model": "claude-sonnet-4-5-20250929"},
    )

    assert model_with_config.model == "claude-sonnet-4-5-20250929"  # type: ignore[attr-defined]

    expected: dict[str, Any] = {
        "name": None,
        "bound": {
            "name": None,
            "disable_streaming": False,
            "effort": None,
            "model": "claude-sonnet-4-5-20250929",
            "mcp_servers": None,
            "max_tokens": 64000,
            "temperature": None,
            "thinking": None,
            "top_k": None,
            "top_p": None,
            "default_request_timeout": None,
            "max_retries": 2,
            "stop_sequences": None,
            "anthropic_api_url": "https://api.anthropic.com",
            "anthropic_proxy": None,
            "context_management": None,
            "anthropic_api_key": SecretStr("bar"),
            "betas": None,
            "default_headers": None,
            "model_kwargs": {},
            "reuse_last_container": None,
            "inference_geo": None,
            "streaming": False,
            "stream_usage": True,
            "output_version": None,
            "output_config": None,
        },
        "kwargs": {
            "tools": [{"name": "foo", "description": "foo", "input_schema": {}}],
        },
        "config": {
            "callbacks": None,
            "configurable": {},
            "metadata": {},
            "recursion_limit": 25,
            "tags": ["foo"],
        },
        "config_factories": [],
        "custom_input_type": None,
        "custom_output_type": None,
    }
    assert model_with_config.model_dump() == expected  # type: ignore[attr-defined]
    prompt = ChatPromptTemplate.from_messages([("system", "foo")])
    chain = prompt | model_with_config
    assert isinstance(chain, RunnableSequence)