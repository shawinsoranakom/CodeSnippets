def test_mcp_builtin_zdr_v1() -> None:
    llm = ChatOpenAI(
        model="gpt-5-nano",
        output_version="v1",
        store=False,
        include=["reasoning.encrypted_content"],
    )

    llm_with_tools = llm.bind_tools(
        [
            {
                "type": "mcp",
                "server_label": "deepwiki",
                "server_url": "https://mcp.deepwiki.com/mcp",
                "allowed_tools": ["ask_question"],
                "require_approval": "always",
            }
        ]
    )
    input_message = {
        "role": "user",
        "content": (
            "What transport protocols does the 2025-03-26 version of the MCP "
            "spec (modelcontextprotocol/modelcontextprotocol) support?"
        ),
    }
    full: BaseMessageChunk | None = None
    for chunk in llm_with_tools.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk

    assert isinstance(full, AIMessageChunk)
    assert all(isinstance(block, dict) for block in full.content)

    approval_message = HumanMessage(
        [
            {
                "type": "non_standard",
                "value": {
                    "type": "mcp_approval_response",
                    "approve": True,
                    "approval_request_id": block["value"]["id"],  # type: ignore[index]
                },
            }
            for block in full.content_blocks
            if block["type"] == "non_standard"
            and block["value"]["type"] == "mcp_approval_request"  # type: ignore[index]
        ]
    )
    result = llm_with_tools.invoke([input_message, full, approval_message])
    next_message = {"role": "user", "content": "Thanks!"}
    _ = llm_with_tools.invoke(
        [input_message, full, approval_message, result, next_message]
    )