def verify_harmony_messages(
    messages: list[Any], expected_messages: list[dict[str, Any]]
):
    assert len(messages) == len(expected_messages)
    for msg, expected in zip(messages, expected_messages):
        if "role" in expected:
            assert msg.author.role == expected["role"]
        if "author_name" in expected:
            assert msg.author.name == expected["author_name"]
        if "channel" in expected:
            assert msg.channel == expected["channel"]
        if "recipient" in expected:
            assert msg.recipient == expected["recipient"]
        if "content" in expected:
            assert msg.content[0].text == expected["content"]
        if "content_type" in expected:
            assert msg.content_type == expected["content_type"]
        if "tool_definitions" in expected:
            # Check that the tool definitions match the expected list of tool names
            actual_tools = [t.name for t in msg.content[0].tools["functions"].tools]
            assert actual_tools == expected["tool_definitions"]