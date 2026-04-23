def _expand_edge(
    compact_edge: CompactEdge,
    expanded_nodes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Expand a compact edge to full edge format.

    Args:
        compact_edge: The compact edge to expand
        expanded_nodes: Dict of node_id -> expanded node data

    Returns:
        Full edge data structure
    """
    source_node = expanded_nodes.get(compact_edge.source)
    target_node = expanded_nodes.get(compact_edge.target)

    if not source_node:
        msg = f"Source node '{compact_edge.source}' not found"
        raise ValueError(msg)
    if not target_node:
        msg = f"Target node '{compact_edge.target}' not found"
        raise ValueError(msg)

    source_node_data = source_node["data"]["node"]
    target_node_data = target_node["data"]["node"]

    # Find output types from source node
    source_outputs = source_node_data.get("outputs", [])
    source_output = next(
        (o for o in source_outputs if o.get("name") == compact_edge.source_output),
        None,
    )
    output_types = source_output.get("types", []) if source_output else []

    # If no outputs defined, use base_classes
    if not output_types:
        output_types = source_node_data.get("base_classes", [])

    # Find input types and field type from target node template
    target_template = target_node_data.get("template", {})
    target_field = target_template.get(compact_edge.target_input, {})
    input_types = target_field.get("input_types", [])
    field_type = target_field.get("type", "str") if isinstance(target_field, dict) else "str"
    if not input_types and isinstance(target_field, dict):
        input_types = [field_type]

    source_type = source_node["data"]["type"]

    # Build handle data objects
    source_handle_data = _build_source_handle_data(
        compact_edge.source,
        source_type,
        compact_edge.source_output,
        output_types,
    )
    target_handle_data = _build_target_handle_data(
        compact_edge.target,
        compact_edge.target_input,
        input_types,
        field_type,
    )

    # Encode handles to string format
    source_handle_str = _encode_handle(source_handle_data)
    target_handle_str = _encode_handle(target_handle_data)

    edge_id = f"reactflow__edge-{compact_edge.source}{source_handle_str}-{compact_edge.target}{target_handle_str}"

    return {
        "source": compact_edge.source,
        "sourceHandle": source_handle_str,
        "target": compact_edge.target,
        "targetHandle": target_handle_str,
        "id": edge_id,
        "data": {
            "sourceHandle": source_handle_data,
            "targetHandle": target_handle_data,
        },
        "className": "",
        "selected": False,
        "animated": False,
    }