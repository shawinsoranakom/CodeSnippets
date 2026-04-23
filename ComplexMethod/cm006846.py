def _analyze_graph_structure(graph: Graph) -> dict[str, Any]:
    """Analyze the graph structure to extract dynamic documentation information.

    Args:
        graph: The LFX graph to analyze

    Returns:
        dict: Graph analysis including components, input/output types, and flow details
    """
    analysis: dict[str, Any] = {
        "components": [],
        "input_types": set(),
        "output_types": set(),
        "node_count": 0,
        "edge_count": 0,
        "entry_points": [],
        "exit_points": [],
    }

    try:
        # Analyze nodes
        for node_id, node in graph.nodes.items():
            analysis["node_count"] += 1
            component_info = {
                "id": node_id,
                "type": node.data.get("type", "Unknown"),
                "name": node.data.get("display_name", node.data.get("type", "Unknown")),
                "description": node.data.get("description", ""),
                "template": node.data.get("template", {}),
            }
            analysis["components"].append(component_info)

            # Identify entry points (nodes with no incoming edges)
            if not any(edge.source == node_id for edge in graph.edges):
                analysis["entry_points"].append(component_info)

            # Identify exit points (nodes with no outgoing edges)
            if not any(edge.target == node_id for edge in graph.edges):
                analysis["exit_points"].append(component_info)

        # Analyze edges
        analysis["edge_count"] = len(graph.edges)

        # Try to determine input/output types from entry/exit points
        for entry in analysis["entry_points"]:
            template = entry.get("template", {})
            for field_config in template.values():
                if field_config.get("type") in ["str", "text", "string"]:
                    analysis["input_types"].add("text")
                elif field_config.get("type") in ["int", "float", "number"]:
                    analysis["input_types"].add("numeric")
                elif field_config.get("type") in ["file", "path"]:
                    analysis["input_types"].add("file")

        for exit_point in analysis["exit_points"]:
            template = exit_point.get("template", {})
            for field_config in template.values():
                if field_config.get("type") in ["str", "text", "string"]:
                    analysis["output_types"].add("text")
                elif field_config.get("type") in ["int", "float", "number"]:
                    analysis["output_types"].add("numeric")
                elif field_config.get("type") in ["file", "path"]:
                    analysis["output_types"].add("file")

    except (KeyError, AttributeError):
        # If analysis fails, provide basic info
        analysis["components"] = [{"type": "Unknown", "name": "Graph Component"}]
        analysis["input_types"] = {"text"}
        analysis["output_types"] = {"text"}

    # Convert sets to lists for JSON serialization
    analysis["input_types"] = list(analysis["input_types"])
    analysis["output_types"] = list(analysis["output_types"])

    return analysis