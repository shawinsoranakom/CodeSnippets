def test_should_isolate_inputs_when_tool_invoked_concurrently():
    """Bug #8791: concurrent tool invocations must not share mutable state.

    GIVEN: A component converted to a StructuredTool via ComponentToolkit
    WHEN:  The tool is invoked concurrently with different inputs
    THEN:  Each invocation must see its own inputs (no cross-contamination)
    """
    # Arrange
    component = SlowLabelComponent()
    toolkit = ComponentToolkit(component=component)
    tools = toolkit.get_tools()
    assert len(tools) == 1
    tool = tools[0]

    results = []

    def invoke_tool(product_id: str, label: str) -> None:
        result = tool.invoke({"product_id": product_id, "label": label})
        results.append(result)

    # Act - invoke the same tool concurrently with different inputs
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(invoke_tool, "PROD-001", "Electronics")
        future2 = executor.submit(invoke_tool, "PROD-002", "Clothing")
        future1.result()
        future2.result()

    # Assert - each invocation must retain its own inputs throughout execution
    assert len(results) == 2

    for result in results:
        # Inputs captured before and after the delay must be identical
        assert result["product_id_before"] == result["product_id_after"], (
            f"product_id changed during execution: '{result['product_id_before']}' -> '{result['product_id_after']}'"
        )
        assert result["label_before"] == result["label_after"], (
            f"label changed during execution: '{result['label_before']}' -> '{result['label_after']}'"
        )

    # Both products must have been processed (not duplicated)
    product_ids = {r["product_id_before"] for r in results}
    assert product_ids == {"PROD-001", "PROD-002"}, (
        f"Expected both products to be processed independently, got: {product_ids}"
    )