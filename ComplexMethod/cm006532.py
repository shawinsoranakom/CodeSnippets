def run_response_to_workflow_response(
    run_response: RunResponse,
    flow_id: str,
    job_id: str,
    workflow_request: WorkflowExecutionRequest,
    graph: Graph,
) -> WorkflowExecutionResponse:
    """Convert V1 RunResponse to V2 WorkflowExecutionResponse.

    This function transforms the V1 execution response to the new V2 schema format.
    It intelligently handles different node types and determines what content to expose.

    Terminal Node Processing Logic:
        1. Identifies all terminal nodes (vertices with no successors)
        2. For each terminal node:
           - Output nodes (is_output=True): Full content is exposed
           - Data/DataFrame nodes: Content is exposed regardless of is_output flag
           - Message nodes (non-output): Only metadata is exposed (source, file_path)

    Output Key Selection:
        - Uses vertex.display_name as the primary key for outputs
        - Falls back to vertex.id if duplicate display_names are detected
        - Stores original display_name in metadata when using id as key

    Args:
        run_response: The V1 response from simple_run_flow containing execution results
        flow_id: The flow identifier
        job_id: The generated job ID for tracking this execution
        workflow_request: Original workflow request (inputs are echoed back in response)
        graph: The Graph instance used for terminal node detection and vertex metadata

    Returns:
        WorkflowExecutionResponse: V2 schema response with structured outputs

    Example:
        Terminal nodes: ["ChatOutput-abc", "LLM-xyz", "DataNode-123"]
        - ChatOutput-abc (is_output=True, type=message): Full content exposed
        - LLM-xyz (is_output=False, type=message): Only metadata (model source)
        - DataNode-123 (is_output=False, type=data): Full content exposed
    """
    # Get terminal nodes (vertices with no successors)
    try:
        terminal_node_ids = graph.get_terminal_nodes()
    except AttributeError:
        # Fallback: manually check successor_map
        terminal_node_ids = [vertex.id for vertex in graph.vertices if not graph.successor_map.get(vertex.id, [])]

    # Build output data map from run_response using component_id as key
    # This ensures unique keys even when components have duplicate display_names
    output_data_map: dict[str, Any] = {}
    if run_response.outputs:
        for run_output in run_response.outputs:
            if hasattr(run_output, "outputs") and run_output.outputs:
                for result_data in run_output.outputs:
                    if not result_data:
                        continue
                    # Use component_id as key to ensure uniqueness
                    component_id = result_data.component_id if hasattr(result_data, "component_id") else None
                    if component_id:
                        output_data_map[component_id] = result_data

    # Collect all terminal vertices
    terminal_vertices = [graph.get_vertex(vertex_id) for vertex_id in terminal_node_ids]

    # Process each terminal vertex
    outputs: dict[str, ComponentOutput] = {}
    for vertex in terminal_vertices:
        output_key, component_output = _process_terminal_vertex(vertex, output_data_map)
        outputs[output_key] = component_output

    return WorkflowExecutionResponse(
        flow_id=flow_id,
        job_id=job_id,
        object="response",
        status=JobStatus.COMPLETED,
        errors=[],
        inputs=workflow_request.inputs or {},
        outputs=outputs,
        metadata={},
    )