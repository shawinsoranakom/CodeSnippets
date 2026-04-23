def test_fine_grained_tool_streaming() -> None:
    """Test fine-grained tool streaming reduces latency for tool parameter streaming.

    Fine-grained tool streaming enables Claude to stream tool parameter values.

    https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming
    """
    llm = ChatAnthropic(
        model=MODEL_NAME,  # type: ignore[call-arg]
        temperature=0,
        betas=["fine-grained-tool-streaming-2025-05-14"],
    )

    # Define a tool that requires a longer text parameter
    tool_definition = {
        "name": "write_document",
        "description": "Write a document with the given content",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "content": {
                    "type": "string",
                    "description": "The full document content",
                },
            },
            "required": ["title", "content"],
        },
    }

    llm_with_tools = llm.bind_tools([tool_definition])
    query = (
        "Write a document about the benefits of streaming APIs. "
        "Include at least 3 paragraphs."
    )

    # Test streaming with fine-grained tool streaming
    first = True
    chunks: list[BaseMessage | BaseMessageChunk] = []
    tool_call_chunks = []

    for chunk in llm_with_tools.stream(query):
        chunks.append(chunk)
        if first:
            gathered = chunk
            first = False
        else:
            gathered = gathered + chunk  # type: ignore[assignment]

        # Collect tool call chunks
        tool_call_chunks.extend(
            [
                block
                for block in chunk.content_blocks
                if block["type"] == "tool_call_chunk"
            ]
        )

    # Verify we got chunks
    assert len(chunks) > 1

    # Verify final message has tool call
    assert isinstance(gathered, AIMessageChunk)
    assert isinstance(gathered.tool_calls, list)
    assert len(gathered.tool_calls) >= 1

    # Find the write_document tool call
    write_doc_call = None
    for tool_call in gathered.tool_calls:
        if tool_call["name"] == "write_document":
            write_doc_call = tool_call
            break

    assert write_doc_call is not None, "write_document tool call not found"
    assert isinstance(write_doc_call["args"], dict)
    assert "title" in write_doc_call["args"]
    assert "content" in write_doc_call["args"]
    assert (
        len(write_doc_call["args"]["content"]) > 100
    )  # Should have substantial content

    # Verify tool_call_chunks were received
    # With fine-grained streaming, we should get tool call chunks
    assert len(tool_call_chunks) > 0

    # Verify content_blocks in final message
    content_blocks = gathered.content_blocks
    assert len(content_blocks) >= 1

    # Should have at least one tool_call block
    tool_call_blocks = [b for b in content_blocks if b["type"] == "tool_call"]
    assert len(tool_call_blocks) >= 1

    write_doc_block = None
    for block in tool_call_blocks:
        if block["name"] == "write_document":
            write_doc_block = block
            break

    assert write_doc_block is not None
    assert write_doc_block["name"] == "write_document"
    assert "args" in write_doc_block