def test_remote_mcp(output_version: Literal["v0", "v1"]) -> None:
    """Note: this is a beta feature.

    TODO: Update to remove beta once generally available.
    """
    mcp_servers = [
        {
            "type": "url",
            "url": "https://mcp.deepwiki.com/mcp",
            "name": "deepwiki",
            "authorization_token": "PLACEHOLDER",
        },
    ]

    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",  # type: ignore[call-arg]
        mcp_servers=mcp_servers,
        output_version=output_version,
    ).bind_tools([{"type": "mcp_toolset", "mcp_server_name": "deepwiki"}])

    input_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "What transport protocols does the 2025-03-26 version of the MCP "
                    "spec (modelcontextprotocol/modelcontextprotocol) support?"
                ),
            },
        ],
    }
    response = llm.invoke([input_message])
    assert all(isinstance(block, dict) for block in response.content)
    block_types = {block["type"] for block in response.content}  # type: ignore[index]
    if output_version == "v0":
        assert block_types == {"text", "mcp_tool_use", "mcp_tool_result"}
    else:
        assert block_types == {"text", "server_tool_call", "server_tool_result"}

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    assert all(isinstance(block, dict) for block in full.content)
    block_types = {block["type"] for block in full.content}  # type: ignore[index]
    if output_version == "v0":
        assert block_types == {"text", "mcp_tool_use", "mcp_tool_result"}
    else:
        assert block_types == {"text", "server_tool_call", "server_tool_result"}

    # Test we can pass back in
    next_message = {
        "role": "user",
        "content": "Please query the same tool again, but add 'please' to your query.",
    }
    _ = llm.invoke(
        [input_message, full, next_message],
    )