def test_code_execution_old(output_version: Literal["v0", "v1"]) -> None:
    """Note: this tests the `code_execution_20250522` tool, which is now legacy.

    See the `test_code_execution` test below to test the current
    `code_execution_20250825` tool.

    Migration guide: https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#upgrade-to-latest-tool-version
    """
    llm = ChatAnthropic(
        model=MODEL_NAME,  # type: ignore[call-arg]
        betas=["code-execution-2025-05-22"],
        output_version=output_version,
    )

    tool = {"type": "code_execution_20250522", "name": "code_execution"}
    llm_with_tools = llm.bind_tools([tool])

    input_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": (
                    "Calculate the mean and standard deviation of "
                    "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
                ),
            },
        ],
    }
    response = llm_with_tools.invoke([input_message])
    assert all(isinstance(block, dict) for block in response.content)
    block_types = {block["type"] for block in response.content}  # type: ignore[index]
    if output_version == "v0":
        assert block_types == {"text", "server_tool_use", "code_execution_tool_result"}
    else:
        assert block_types == {"text", "server_tool_call", "server_tool_result"}

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm_with_tools.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    block_types = {block["type"] for block in full.content}  # type: ignore[index]
    if output_version == "v0":
        assert block_types == {"text", "server_tool_use", "code_execution_tool_result"}
    else:
        assert block_types == {"text", "server_tool_call", "server_tool_result"}

    # Test we can pass back in
    next_message = {
        "role": "user",
        "content": "Please add more comments to the code.",
    }
    _ = llm_with_tools.invoke(
        [input_message, full, next_message],
    )