def test_code_interpreter(output_version: Literal["v0", "responses/v1", "v1"]) -> None:
    llm = ChatOpenAI(
        model="o4-mini", use_responses_api=True, output_version=output_version
    )
    llm_with_tools = llm.bind_tools(
        [{"type": "code_interpreter", "container": {"type": "auto"}}]
    )
    input_message = {
        "role": "user",
        "content": "Write and run code to answer the question: what is 3^3?",
    }
    response = llm_with_tools.invoke([input_message])
    assert isinstance(response, AIMessage)
    _check_response(response)
    if output_version == "v0":
        tool_outputs = [
            item
            for item in response.additional_kwargs["tool_outputs"]
            if item["type"] == "code_interpreter_call"
        ]
        assert len(tool_outputs) == 1
    elif output_version == "responses/v1":
        tool_outputs = [
            item
            for item in response.content
            if isinstance(item, dict) and item["type"] == "code_interpreter_call"
        ]
        assert len(tool_outputs) == 1
    else:
        # v1
        tool_outputs = [
            item
            for item in response.content_blocks
            if item["type"] == "server_tool_call" and item["name"] == "code_interpreter"
        ]
        code_interpreter_result = next(
            item
            for item in response.content_blocks
            if item["type"] == "server_tool_result"
        )
        assert tool_outputs
        assert code_interpreter_result
    assert len(tool_outputs) == 1

    # Test streaming
    # Use same container
    container_id = tool_outputs[0].get("container_id") or tool_outputs[0].get(
        "extras", {}
    ).get("container_id")
    llm_with_tools = llm.bind_tools(
        [{"type": "code_interpreter", "container": container_id}]
    )

    full: BaseMessageChunk | None = None
    for chunk in llm_with_tools.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    if output_version == "v0":
        tool_outputs = [
            item
            for item in response.additional_kwargs["tool_outputs"]
            if item["type"] == "code_interpreter_call"
        ]
        assert tool_outputs
    elif output_version == "responses/v1":
        tool_outputs = [
            item
            for item in response.content
            if isinstance(item, dict) and item["type"] == "code_interpreter_call"
        ]
        assert tool_outputs
    else:
        # v1
        code_interpreter_call = next(
            item
            for item in full.content_blocks
            if item["type"] == "server_tool_call" and item["name"] == "code_interpreter"
        )
        code_interpreter_result = next(
            item for item in full.content_blocks if item["type"] == "server_tool_result"
        )
        assert code_interpreter_call
        assert code_interpreter_result

    # Test we can pass back in
    next_message = {"role": "user", "content": "Please add more comments to the code."}
    _ = llm_with_tools.invoke([input_message, full, next_message])