def test_message_chunks() -> None:
    assert AIMessageChunk(content="I am", id="ai3") + AIMessageChunk(
        content=" indeed."
    ) == AIMessageChunk(content="I am indeed.", id="ai3"), (
        "MessageChunk + MessageChunk should be a MessageChunk"
    )

    assert AIMessageChunk(content="I am", id="ai2") + HumanMessageChunk(
        content=" indeed.", id="human1"
    ) == AIMessageChunk(content="I am indeed.", id="ai2"), (
        "MessageChunk + MessageChunk should be a MessageChunk "
        "of same class as the left side"
    )

    assert AIMessageChunk(
        content="", additional_kwargs={"foo": "bar"}
    ) + AIMessageChunk(content="", additional_kwargs={"baz": "foo"}) == AIMessageChunk(
        content="", additional_kwargs={"foo": "bar", "baz": "foo"}
    ), (
        "MessageChunk + MessageChunk should be a MessageChunk "
        "with merged additional_kwargs"
    )

    assert AIMessageChunk(
        content="", additional_kwargs={"function_call": {"name": "web_search"}}
    ) + AIMessageChunk(
        content="", additional_kwargs={"function_call": {"arguments": None}}
    ) + AIMessageChunk(
        content="", additional_kwargs={"function_call": {"arguments": "{\n"}}
    ) + AIMessageChunk(
        content="",
        additional_kwargs={"function_call": {"arguments": '  "query": "turtles"\n}'}},
    ) == AIMessageChunk(
        content="",
        additional_kwargs={
            "function_call": {
                "name": "web_search",
                "arguments": '{\n  "query": "turtles"\n}',
            }
        },
    ), (
        "MessageChunk + MessageChunk should be a MessageChunk "
        "with merged additional_kwargs"
    )

    # Test tool calls
    assert (
        AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name="tool1", args="", id="1", index=0)
            ],
        )
        + AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(
                    name=None, args='{"arg1": "val', id=None, index=0
                )
            ],
        )
        + AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name=None, args='ue}"', id=None, index=0)
            ],
        )
    ) == AIMessageChunk(
        content="",
        tool_call_chunks=[
            create_tool_call_chunk(
                name="tool1", args='{"arg1": "value}"', id="1", index=0
            )
        ],
    )

    assert (
        AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name="tool1", args="", id="1", index=0)
            ],
        )
        + AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name=None, args='{"arg1": "val', id="", index=0)
            ],
        )
        + AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name=None, args='ue"}', id="", index=0)
            ],
        )
    ) == AIMessageChunk(
        content="",
        tool_call_chunks=[
            create_tool_call_chunk(
                name="tool1", args='{"arg1": "value"}', id="1", index=0
            )
        ],
    )

    assert (
        AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name="tool1", args="", id="1", index=0)
            ],
        )
        + AIMessageChunk(
            content="",
            tool_call_chunks=[
                create_tool_call_chunk(name="tool1", args="a", id=None, index=1)
            ],
        )
        # Don't merge if `index` field does not match.
    ) == AIMessageChunk(
        content="",
        tool_call_chunks=[
            create_tool_call_chunk(name="tool1", args="", id="1", index=0),
            create_tool_call_chunk(name="tool1", args="a", id=None, index=1),
        ],
    )

    ai_msg_chunk = AIMessageChunk(content="")
    tool_calls_msg_chunk = AIMessageChunk(
        content="",
        tool_call_chunks=[
            create_tool_call_chunk(name="tool1", args="a", id=None, index=1)
        ],
    )
    assert ai_msg_chunk + tool_calls_msg_chunk == tool_calls_msg_chunk
    assert tool_calls_msg_chunk + ai_msg_chunk == tool_calls_msg_chunk

    ai_msg_chunk = AIMessageChunk(
        content="",
        tool_call_chunks=[
            create_tool_call_chunk(name="tool1", args="", id="1", index=0)
        ],
    )
    assert ai_msg_chunk.tool_calls == [create_tool_call(name="tool1", args={}, id="1")]

    # Test token usage
    left = AIMessageChunk(
        content="",
        usage_metadata={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
    )
    right = AIMessageChunk(
        content="",
        usage_metadata={"input_tokens": 4, "output_tokens": 5, "total_tokens": 9},
    )
    assert left + right == AIMessageChunk(
        content="",
        usage_metadata={"input_tokens": 5, "output_tokens": 7, "total_tokens": 12},
    )
    assert AIMessageChunk(content="") + left == left
    assert right + AIMessageChunk(content="") == right

    default_id = "lc_run--abc123"
    meaningful_id = "msg_def456"

    # Test ID order of precedence
    null_id_chunk = AIMessageChunk(content="", id=None)
    default_id_chunk = AIMessageChunk(
        content="", id=default_id
    )  # LangChain-assigned run ID
    provider_chunk = AIMessageChunk(
        content="", id=meaningful_id
    )  # provided ID (either by user or provider)

    assert (null_id_chunk + default_id_chunk).id == default_id
    assert (null_id_chunk + provider_chunk).id == meaningful_id

    # Provider assigned IDs have highest precedence
    assert (default_id_chunk + provider_chunk).id == meaningful_id