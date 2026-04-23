async def test_conditional_router_max_iterations():
    # Chat input initialization
    text_input = TextInputComponent(_id="text_input")

    # Conditional router setup with a condition that will never match
    router = ConditionalRouterComponent(_id="router").set(
        input_text=text_input.text_response,
        match_text="bacon",
        operator="equals",
        true_case_message="This message should not be routed to true_result",
        false_case_message="This message should not be routed to false_result",
        max_iterations=5,
        default_route="true_result",
    )

    # Chat output for the true route
    text_input.set(input_value=router.false_response)

    # Chat output for the false route
    chat_output_false = ChatOutput(_id="chat_output_false")
    chat_output_false.set(input_value=router.true_response)

    # Build the graph
    graph = Graph(text_input, chat_output_false)

    # Assertions for graph cyclicity and correctness
    assert graph.is_cyclic is True, "Graph should contain cycles."

    # Run and validate the execution of the graph
    results = []
    snapshots = [graph.get_snapshot()]
    previous_iteration = graph.context.get("router_iteration", 0)
    async for result in graph.async_start(max_iterations=20, config={"output": {"cache": False}}):
        snapshots.append(graph.get_snapshot())
        results.append(result)
        if hasattr(result, "vertex") and result.vertex.id == "router":
            current_iteration = graph.context.get("router_iteration", 0)
            assert current_iteration == previous_iteration + 1, "Iteration should increment by 1"
            previous_iteration = current_iteration

    # Check if the max_iterations logic is working
    router_id = router._id.lower()
    assert graph.context.get(f"{router_id}_iteration", 0) == 5, "Router should stop after max_iterations"

    # Extract the vertex IDs for analysis
    results_ids = [result.vertex.id for result in results if hasattr(result, "vertex")]
    assert "chat_output_false" in results_ids, f"Expected outputs not in results: {results_ids}"