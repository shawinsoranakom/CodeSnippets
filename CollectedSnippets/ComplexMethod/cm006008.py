async def test_loop_flow():
    """Test that loop_flow creates a working graph with proper loop feedback connection."""
    flow = loop_flow()
    assert flow is not None
    assert flow._start is not None
    assert flow._end is not None

    # Verify all expected components are present
    expected_vertices = {
        "URLComponent",
        "SplitTextComponent",
        "LoopComponent",
        "ParserComponent",
        "PromptComponent",
        "OpenAIModelComponent",
        "StructuredOutputComponent",
        "ChatOutput",
    }

    assert all(vertex.id.split("-")[0] in expected_vertices for vertex in flow.vertices)

    expected_execution_order = [
        "OpenAIModelComponent",
        "URLComponent",
        "SplitTextComponent",
        "LoopComponent",
        "ParserComponent",
        "PromptComponent",
        "StructuredOutputComponent",
        "LoopComponent",
        "ParserComponent",
        "PromptComponent",
        "StructuredOutputComponent",
        "LoopComponent",
        "ParserComponent",
        "PromptComponent",
        "StructuredOutputComponent",
        "LoopComponent",
        "ChatOutput",
    ]
    results = [result async for result in flow.async_start()]
    result_order = [result.vertex.id.split("-")[0] for result in results if hasattr(result, "vertex")]
    assert result_order == expected_execution_order