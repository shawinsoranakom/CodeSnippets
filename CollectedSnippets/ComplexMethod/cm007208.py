def build_flow_from_spec(spec: str) -> dict[str, Any]:
    """Build a flow dict from a text spec. Returns the flow or errors.

    On success: {"flow": <flow_dict>, "name": str, "node_count": int, "edge_count": int}
    On failure: {"error": str, "details": str}
    """
    registry = load_local_registry()

    try:
        parsed = parse_flow_spec(spec)
    except ValueError as e:
        return {"error": "Invalid spec", "details": str(e)}

    # Validate that all component types exist in the registry
    unknown = [n["type"] for n in parsed["nodes"] if n["type"] not in registry]
    if unknown:
        return {
            "error": f"Unknown component types: {unknown}",
            "details": f"Available types (sample): {sorted(registry.keys())[:30]}",
        }

    # Validate node references in edges and config
    try:
        validate_spec_references(parsed)
    except ValueError as e:
        return {"error": str(e), "details": str(e)}

    # Build the flow
    flow = empty_flow(
        name=parsed.get("name", "Untitled Flow"),
        description=parsed.get("description", ""),
    )

    id_map: dict[str, str] = {}

    # Add components
    for node in parsed["nodes"]:
        try:
            result = add_component(flow, node["type"], registry)
        except (ValueError, KeyError) as e:
            return {"error": f"Failed to add component '{node['type']}' (node '{node['id']}')", "details": str(e)}
        id_map[node["id"]] = result["id"]

    # Apply config
    for spec_id, params in parsed.get("config", {}).items():
        try:
            configure_component(flow, id_map[spec_id], params)
        except (ValueError, KeyError) as e:
            return {"error": f"Failed to configure node '{spec_id}'", "details": str(e)}

    # Connect edges
    for edge in parsed["edges"]:
        src_out = f"{edge['source_id']}.{edge['source_output']}"
        tgt_in = f"{edge['target_id']}.{edge['target_input']}"
        try:
            add_connection(
                flow,
                id_map[edge["source_id"]],
                edge["source_output"],
                id_map[edge["target_id"]],
                edge["target_input"],
            )
        except (ValueError, KeyError) as e:
            return {"error": f"Failed to connect {src_out} -> {tgt_in}", "details": str(e)}

    layout_flow(flow)

    flow["name"] = parsed.get("name", "Untitled Flow")
    flow["description"] = parsed.get("description", "")

    return {
        "flow": flow,
        "name": flow["name"],
        "node_count": len(flow["data"]["nodes"]),
        "edge_count": len(flow["data"]["edges"]),
        "node_id_map": id_map,
    }