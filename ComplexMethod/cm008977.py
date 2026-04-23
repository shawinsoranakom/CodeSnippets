def test_summarization_middleware_profile_inference_triggers_summary() -> None:
    """Ensure automatic profile inference triggers summarization when limits are exceeded."""

    def token_counter(messages: Iterable[MessageLikeRepresentation]) -> int:
        return len(list(messages)) * 200

    middleware = SummarizationMiddleware(
        model=ProfileChatModel(),
        trigger=("fraction", 0.81),
        keep=("fraction", 0.5),
        token_counter=token_counter,
    )

    state = AgentState[Any](
        messages=[
            HumanMessage(content="Message 1"),
            AIMessage(content="Message 2"),
            HumanMessage(content="Message 3"),
            AIMessage(content="Message 4"),
        ]
    )

    # Test we don't engage summarization
    # we have total_tokens = 4 * 200 = 800
    # and max_input_tokens = 1000
    # since 0.81 * 1000 == 810 > 800 -> summarization not triggered
    result = middleware.before_model(state, Runtime())
    assert result is None

    # Engage summarization
    # since 0.80 * 1000 == 800 <= 800
    middleware = SummarizationMiddleware(
        model=ProfileChatModel(),
        trigger=("fraction", 0.80),
        keep=("fraction", 0.5),
        token_counter=token_counter,
    )
    result = middleware.before_model(state, Runtime())
    assert result is not None
    assert isinstance(result["messages"][0], RemoveMessage)
    summary_message = result["messages"][1]
    assert isinstance(summary_message, HumanMessage)
    assert summary_message.text.startswith("Here is a summary of the conversation")
    assert len(result["messages"][2:]) == 2  # Preserved messages
    assert [message.content for message in result["messages"][2:]] == [
        "Message 3",
        "Message 4",
    ]

    # With keep=("fraction", 0.6) the target token allowance becomes 600,
    # so the cutoff shifts to keep the last three messages instead of two.
    middleware = SummarizationMiddleware(
        model=ProfileChatModel(),
        trigger=("fraction", 0.80),
        keep=("fraction", 0.6),
        token_counter=token_counter,
    )
    result = middleware.before_model(state, Runtime())
    assert result is not None
    assert [message.content for message in result["messages"][2:]] == [
        "Message 2",
        "Message 3",
        "Message 4",
    ]

    # Once keep=("fraction", 0.8) the inferred limit equals the full
    # context (target tokens = 800), so token-based retention keeps everything
    # and summarization is skipped entirely.
    middleware = SummarizationMiddleware(
        model=ProfileChatModel(),
        trigger=("fraction", 0.80),
        keep=("fraction", 0.8),
        token_counter=token_counter,
    )
    assert middleware.before_model(state, Runtime()) is None

    # Test with tokens_to_keep as absolute int value
    middleware_int = SummarizationMiddleware(
        model=ProfileChatModel(),
        trigger=("fraction", 0.80),
        keep=("tokens", 400),  # Keep exactly 400 tokens (2 messages)
        token_counter=token_counter,
    )
    result = middleware_int.before_model(state, Runtime())
    assert result is not None
    assert [message.content for message in result["messages"][2:]] == [
        "Message 3",
        "Message 4",
    ]

    # Test with tokens_to_keep as larger int value
    middleware_int_large = SummarizationMiddleware(
        model=ProfileChatModel(),
        trigger=("fraction", 0.80),
        keep=("tokens", 600),  # Keep 600 tokens (3 messages)
        token_counter=token_counter,
    )
    result = middleware_int_large.before_model(state, Runtime())
    assert result is not None
    assert [message.content for message in result["messages"][2:]] == [
        "Message 2",
        "Message 3",
        "Message 4",
    ]