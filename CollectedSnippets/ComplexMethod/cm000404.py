def _build_execution_summary(
    node_executions: list[NodeExecutionResult],
    execution_stats: GraphExecutionStats,
    graph_name: str,
    graph_description: str,
    graph_links: list[Any],
    execution_status: ExecutionStatus | None = None,
) -> dict[str, Any]:
    """Build a structured summary of execution data for AI analysis."""

    nodes: list[NodeInfo] = []
    node_execution_counts: dict[str, int] = {}
    node_error_counts: dict[str, int] = {}
    node_errors: dict[str, list[ErrorInfo]] = {}
    node_outputs: dict[str, list[InputOutputInfo]] = {}
    node_inputs: dict[str, list[InputOutputInfo]] = {}
    input_output_data: dict[str, Any] = {}
    node_map: dict[str, NodeInfo] = {}

    # Process node executions
    for node_exec in node_executions:
        block = get_block(node_exec.block_id)
        if not block:
            logger.warning(
                f"Block {node_exec.block_id} not found for node {node_exec.node_id}"
            )
            continue

        # Track execution counts per node
        if node_exec.node_id not in node_execution_counts:
            node_execution_counts[node_exec.node_id] = 0
        node_execution_counts[node_exec.node_id] += 1

        # Track errors per node and group them
        if node_exec.status == ExecutionStatus.FAILED:
            if node_exec.node_id not in node_error_counts:
                node_error_counts[node_exec.node_id] = 0
            node_error_counts[node_exec.node_id] += 1

            # Extract actual error message from output_data
            error_message = "Unknown error"
            if node_exec.output_data and isinstance(node_exec.output_data, dict):
                # Check if error is in output_data
                if "error" in node_exec.output_data:
                    error_output = node_exec.output_data["error"]
                    if isinstance(error_output, list) and error_output:
                        error_message = str(error_output[0])
                    else:
                        error_message = str(error_output)

            # Group errors by node_id
            if node_exec.node_id not in node_errors:
                node_errors[node_exec.node_id] = []

            node_errors[node_exec.node_id].append(
                {
                    "error": error_message,
                    "execution_id": _truncate_uuid(node_exec.node_exec_id),
                    "timestamp": node_exec.add_time.isoformat(),
                }
            )

        # Collect output samples for each node (latest executions)
        if node_exec.output_data:
            if node_exec.node_id not in node_outputs:
                node_outputs[node_exec.node_id] = []

            # Truncate output data to 100 chars to save space
            truncated_output = truncate(node_exec.output_data, 100)

            node_outputs[node_exec.node_id].append(
                {
                    "execution_id": _truncate_uuid(node_exec.node_exec_id),
                    "output_data": truncated_output,
                    "timestamp": node_exec.add_time.isoformat(),
                }
            )

        # Collect input samples for each node (latest executions)
        if node_exec.input_data:
            if node_exec.node_id not in node_inputs:
                node_inputs[node_exec.node_id] = []

            # Truncate input data to 100 chars to save space
            truncated_input = truncate(node_exec.input_data, 100)

            node_inputs[node_exec.node_id].append(
                {
                    "execution_id": _truncate_uuid(node_exec.node_exec_id),
                    "output_data": truncated_input,  # Reuse field name for consistency
                    "timestamp": node_exec.add_time.isoformat(),
                }
            )

        # Build node data (only add unique nodes)
        if node_exec.node_id not in node_map:
            node_data: NodeInfo = {
                "node_id": _truncate_uuid(node_exec.node_id),
                "block_id": _truncate_uuid(node_exec.block_id),
                "block_name": block.name,
                "block_description": block.description or "",
                "execution_count": 0,  # Will be set later
                "error_count": 0,  # Will be set later
                "recent_errors": [],  # Will be set later
                "recent_outputs": [],  # Will be set later
                "recent_inputs": [],  # Will be set later
            }
            nodes.append(node_data)
            node_map[node_exec.node_id] = node_data

        # Store input/output data for special blocks (input/output blocks)
        if block.name in ["AgentInputBlock", "AgentOutputBlock", "UserInputBlock"]:
            if node_exec.input_data:
                input_output_data[f"{node_exec.node_id}_inputs"] = dict(
                    node_exec.input_data
                )
            if node_exec.output_data:
                input_output_data[f"{node_exec.node_id}_outputs"] = dict(
                    node_exec.output_data
                )

    # Add execution and error counts to node data, plus limited errors and output samples
    for node in nodes:
        # Use original node_id for lookups (before truncation)
        original_node_id = None
        for orig_id, node_data in node_map.items():
            if node_data == node:
                original_node_id = orig_id
                break

        if original_node_id:
            node["execution_count"] = node_execution_counts.get(original_node_id, 0)
            node["error_count"] = node_error_counts.get(original_node_id, 0)

            # Add limited errors for this node (latest 10 or first 5 + last 5)
            if original_node_id in node_errors:
                node_error_list = node_errors[original_node_id]
                if len(node_error_list) <= 10:
                    node["recent_errors"] = node_error_list
                else:
                    # First 5 + last 5 if more than 10 errors
                    node["recent_errors"] = node_error_list[:5] + node_error_list[-5:]

            # Add latest output samples (latest 3)
            if original_node_id in node_outputs:
                node_output_list = node_outputs[original_node_id]
                # Sort by timestamp if available, otherwise take last 3
                if node_output_list and node_output_list[0].get("timestamp"):
                    node_output_list.sort(
                        key=lambda x: x.get("timestamp", ""), reverse=True
                    )
                node["recent_outputs"] = node_output_list[:3]

            # Add latest input samples (latest 3)
            if original_node_id in node_inputs:
                node_input_list = node_inputs[original_node_id]
                # Sort by timestamp if available, otherwise take last 3
                if node_input_list and node_input_list[0].get("timestamp"):
                    node_input_list.sort(
                        key=lambda x: x.get("timestamp", ""), reverse=True
                    )
                node["recent_inputs"] = node_input_list[:3]

    # Build node relations from graph links
    node_relations: list[NodeRelation] = []
    for link in graph_links:
        # Include link details with source and sink information (truncated UUIDs)
        relation: NodeRelation = {
            "source_node_id": _truncate_uuid(link.source_id),
            "sink_node_id": _truncate_uuid(link.sink_id),
            "source_name": link.source_name,
            "sink_name": link.sink_name,
            "is_static": link.is_static if hasattr(link, "is_static") else False,
        }

        # Add block names if nodes exist in our map
        if link.source_id in node_map:
            relation["source_block_name"] = node_map[link.source_id]["block_name"]
        if link.sink_id in node_map:
            relation["sink_block_name"] = node_map[link.sink_id]["block_name"]

        node_relations.append(relation)

    # Build overall summary
    return {
        "graph_info": {"name": graph_name, "description": graph_description},
        "nodes": nodes,
        "node_relations": node_relations,
        "input_output_data": input_output_data,
        "overall_status": {
            "total_nodes_in_graph": len(nodes),
            "total_executions": execution_stats.node_count,
            "total_errors": execution_stats.node_error_count,
            "execution_time_seconds": execution_stats.walltime,
            "has_errors": bool(
                execution_stats.error or execution_stats.node_error_count > 0
            ),
            "graph_error": (
                str(execution_stats.error) if execution_stats.error else None
            ),
            "graph_execution_status": (
                execution_status.value if execution_status else None
            ),
        },
    }