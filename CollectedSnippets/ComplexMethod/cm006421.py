def json_schema_from_flow(flow: Flow) -> dict:
    """Generate JSON schema from flow input nodes."""
    from lfx.graph.graph.base import Graph

    # Get the flow's data which contains the nodes and their configurations
    flow_data = flow.data or {}

    graph = Graph.from_payload(flow_data)
    input_nodes = [vertex for vertex in graph.vertices if vertex.is_input]

    properties = {}
    required = []
    for node in input_nodes:
        node_data = node.data["node"]
        template = node_data["template"]

        for field_name, field_data in template.items():
            if isinstance(field_data, dict) and field_data.get("show", False) and not field_data.get("advanced", False):
                field_type = field_data.get("type", "string")
                properties[field_name] = {
                    "type": field_type,
                    "description": field_data.get("info", f"Input for {field_name}"),
                }
                # Update field_type in properties after determining the JSON Schema type
                if field_type == "str":
                    field_type = "string"
                elif field_type == "int":
                    field_type = "integer"
                elif field_type == "float":
                    field_type = "number"
                elif field_type == "bool":
                    field_type = "boolean"
                else:
                    logger.warning(f"Unknown field type: {field_type} defaulting to string")
                    field_type = "string"
                properties[field_name]["type"] = field_type

                if field_data.get("required", False):
                    required.append(field_name)

    return {"type": "object", "properties": properties, "required": required}