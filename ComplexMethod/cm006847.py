def _generate_dynamic_run_description(graph: Graph) -> str:
    """Generate dynamic description for the /run endpoint based on graph analysis.

    Args:
        graph: The LFX graph

    Returns:
        str: Dynamic description for the /run endpoint
    """
    analysis = _analyze_graph_structure(graph)

    # Determine input examples based on entry points
    input_examples = []
    for entry in analysis["entry_points"]:
        template = entry.get("template", {})
        for field_name, field_config in template.items():
            if field_config.get("type") in ["str", "text", "string"]:
                input_examples.append(f'"{field_name}": "Your input text here"')
            elif field_config.get("type") in ["int", "float", "number"]:
                input_examples.append(f'"{field_name}": 42')
            elif field_config.get("type") in ["file", "path"]:
                input_examples.append(f'"{field_name}": "/path/to/file.txt"')

    if not input_examples:
        input_examples = ['"input_value": "Your input text here"']

    # Determine output examples based on exit points
    output_examples = []
    for exit_point in analysis["exit_points"]:
        template = exit_point.get("template", {})
        for field_name, field_config in template.items():
            if field_config.get("type") in ["str", "text", "string"]:
                output_examples.append(f'"{field_name}": "Processed result"')
            elif field_config.get("type") in ["int", "float", "number"]:
                output_examples.append(f'"{field_name}": 123')
            elif field_config.get("type") in ["file", "path"]:
                output_examples.append(f'"{field_name}": "/path/to/output.txt"')

    if not output_examples:
        output_examples = ['"result": "Processed result"']

    description_parts = [
        f"Execute the deployed LFX graph with {analysis['node_count']} components.",
        "",
        "**Graph Analysis**:",
        f"- Entry points: {len(analysis['entry_points'])}",
        f"- Exit points: {len(analysis['exit_points'])}",
        f"- Input types: {', '.join(analysis['input_types']) if analysis['input_types'] else 'text'}",
        f"- Output types: {', '.join(analysis['output_types']) if analysis['output_types'] else 'text'}",
        "",
        "**Authentication Required**: Include your API key in the `x-api-key` header or as a query parameter.",
        "",
        "**Example Request**:",
        "```json",
        "{",
        f"  {', '.join(input_examples)}",
        "}",
        "```",
        "",
        "**Example Response**:",
        "```json",
        "{",
        f"  {', '.join(output_examples)},",
        '  "success": true,',
        '  "logs": "Graph execution completed successfully",',
        '  "type": "message",',
        '  "component": "FinalComponent"',
        "}",
        "```",
    ]

    return "\n".join(description_parts)