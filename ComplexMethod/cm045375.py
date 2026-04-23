async def test_chat_completion_context_declarative() -> None:
    unbounded_context = UnboundedChatCompletionContext()
    buffered_context = BufferedChatCompletionContext(buffer_size=5)
    head_tail_context = HeadAndTailChatCompletionContext(head_size=3, tail_size=2)
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key="test_key")
    token_limited_context = TokenLimitedChatCompletionContext(model_client=model_client, token_limit=5)

    # Test serialization
    unbounded_config = unbounded_context.dump_component()
    assert unbounded_config.provider == "autogen_core.model_context.UnboundedChatCompletionContext"

    buffered_config = buffered_context.dump_component()
    assert buffered_config.provider == "autogen_core.model_context.BufferedChatCompletionContext"
    assert buffered_config.config["buffer_size"] == 5

    head_tail_config = head_tail_context.dump_component()
    assert head_tail_config.provider == "autogen_core.model_context.HeadAndTailChatCompletionContext"
    assert head_tail_config.config["head_size"] == 3
    assert head_tail_config.config["tail_size"] == 2

    token_limited_config = token_limited_context.dump_component()
    assert token_limited_config.provider == "autogen_core.model_context.TokenLimitedChatCompletionContext"
    assert token_limited_config.config["token_limit"] == 5
    assert (
        token_limited_config.config["model_client"]["provider"]
        == "autogen_ext.models.openai.OpenAIChatCompletionClient"
    )

    # Test deserialization
    loaded_unbounded = ComponentLoader.load_component(unbounded_config, UnboundedChatCompletionContext)
    assert isinstance(loaded_unbounded, UnboundedChatCompletionContext)

    loaded_buffered = ComponentLoader.load_component(buffered_config, BufferedChatCompletionContext)

    assert isinstance(loaded_buffered, BufferedChatCompletionContext)

    loaded_head_tail = ComponentLoader.load_component(head_tail_config, HeadAndTailChatCompletionContext)

    assert isinstance(loaded_head_tail, HeadAndTailChatCompletionContext)

    loaded_token_limited = ComponentLoader.load_component(token_limited_config, TokenLimitedChatCompletionContext)
    assert isinstance(loaded_token_limited, TokenLimitedChatCompletionContext)