async def test_component_build_results():
    """Test that build_results correctly generates output results and artifacts for defined outputs.

    Test that the results dictionary contains the correct output keys and values,
    and that the artifacts dictionary includes the correct types for each output.
    """
    # Create event queue and manager
    queue = asyncio.Queue()
    event_manager = EventManager(queue)

    # Create component
    component = ComponentForTesting()
    component.set_event_manager(event_manager)

    # Add outputs to the component
    component._outputs_map = {
        "text_output": Output(name="text_output", method="get_text"),
        "tool_output": Output(name="tool_output", method="get_tool"),
    }

    component.outputs = [
        Output(name="text_output", method="get_text"),
        Output(name="tool_output", method="get_tool"),
    ]

    # Build results
    results, artifacts = await component._build_results()

    # Verify results
    assert "text_output" in results
    assert results["text_output"] == "test output"
    assert "tool_output" in results
    assert results["tool_output"]["name"] == "test_tool"

    # Verify artifacts
    assert "text_output" in artifacts
    assert "tool_output" in artifacts
    assert artifacts["text_output"]["type"] == "text"