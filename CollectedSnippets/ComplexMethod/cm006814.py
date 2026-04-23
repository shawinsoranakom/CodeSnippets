async def execute_loop_body(
    graph: "Graph",
    data_list: list[Data],
    loop_body_vertex_ids: set[str],
    start_vertex_id: str | None,
    start_edge,
    end_vertex_id: str | None,
    event_manager=None,
) -> list[Data]:
    """Execute loop body for each data item.

    Creates an isolated subgraph for the loop body and executes it
    for each item in the data list, collecting results.

    Args:
        graph: The graph containing the loop
        data_list: List of Data objects to iterate over
        loop_body_vertex_ids: Set of vertex IDs that form the loop body
        start_vertex_id: The vertex ID of the first vertex in the loop body
        start_edge: The edge connecting loop's item output to start vertex (contains target param info)
        end_vertex_id: The vertex ID that feeds back to the loop's item input
        event_manager: Optional event manager to pass to subgraph execution for UI events

    Returns:
        List of Data objects containing results from each iteration
    """
    if not loop_body_vertex_ids:
        return []

    aggregated_results = []

    for item in data_list:
        # Create fresh subgraph for each iteration. This gives clean vertex/edge state
        # while sharing context between iterations (intentional for loop state).
        # Using async context manager ensures proper cleanup of trace tasks on exit.
        async with graph.create_subgraph(loop_body_vertex_ids) as iteration_subgraph:
            # Inject current item into vertex data BEFORE preparing the subgraph.
            # This ensures components have data during build/validation.
            if start_vertex_id and start_edge:
                # Get the target parameter name from the edge
                if not hasattr(start_edge.target_handle, "field_name"):
                    msg = f"Edge target_handle missing field_name attribute for loop item injection: {start_edge}"
                    raise ValueError(msg)
                target_param = start_edge.target_handle.field_name

                # Find and update the start vertex's frontend data before components are built
                for vertex_data in iteration_subgraph._vertices:  # noqa: SLF001
                    if vertex_data.get("id") == start_vertex_id:
                        # Inject the loop item into the vertex's template data
                        if "data" in vertex_data and "node" in vertex_data["data"]:
                            template = vertex_data["data"]["node"].get("template", {})
                            if target_param in template:
                                template[target_param]["value"] = item
                        break

            # Prepare the subgraph - components will be built with the injected data
            iteration_subgraph.prepare()

            # CRITICAL: Also set the value in the vertex's raw_params
            # Fields with type="other" (like HandleInput) are skipped during field param processing
            # They normally get values from edges, but we filtered out the Loop->Parser edge
            # So we must inject the value directly into raw_params
            if start_vertex_id and start_edge:
                start_vertex = iteration_subgraph.get_vertex(start_vertex_id)
                start_vertex.update_raw_params({target_param: item}, overwrite=True)

            # Execute subgraph and collect results
            # Pass event_manager so UI receives events from subgraph execution
            results = []
            async for result in iteration_subgraph.async_start(event_manager=event_manager):
                results.append(result)
                # Stop all on error (as per design decision)
                if hasattr(result, "valid") and not result.valid:
                    msg = f"Error in loop iteration: {result}"
                    raise RuntimeError(msg)

            # Extract output from final result
            output = extract_loop_output(results, end_vertex_id)
            aggregated_results.append(output)

    return aggregated_results