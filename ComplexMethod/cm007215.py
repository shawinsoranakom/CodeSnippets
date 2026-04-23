def add_connection(
    flow: dict,
    source_id: str,
    source_output: str,
    target_id: str,
    target_input: str,
    source_types: list[str] | None = None,
    target_types: list[str] | None = None,
) -> dict:
    """Add a connection (edge) between two components.

    When source_types/target_types are None they are resolved from the flow
    and type-compatibility is enforced.  When the caller passes explicit types
    the check is skipped (the caller is taking responsibility).
    """
    source_type = source_id.rsplit("-", 1)[0] if "-" in source_id else source_id

    # Resolve types from the flow's node data if not explicitly provided
    types_resolved = source_types is None and target_types is None
    if source_types is None:
        source_types = _resolve_output_types(flow, source_id, source_output)
    if target_types is None:
        target_types, target_field_type = _resolve_input_types(flow, target_id, target_input)
    else:
        target_field_type = "str"

    if types_resolved and not types_compatible(source_types, target_types):
        msg = (
            f"Type mismatch: output '{source_output}' on '{source_id}' produces {source_types}, "
            f"but input '{target_input}' on '{target_id}' accepts {target_types}"
        )
        raise ValueError(msg)

    source_handle_dict = {
        "dataType": source_type,
        "id": source_id,
        "name": source_output,
        "output_types": source_types,
    }
    target_handle_dict = {
        "fieldName": target_input,
        "id": target_id,
        "inputTypes": target_types,
        "type": target_field_type,
    }

    source_handle_s = _scaped_json_stringify(source_handle_dict)
    target_handle_s = _scaped_json_stringify(target_handle_dict)

    edge_id = f"reactflow__edge-{source_id}{source_handle_s}-{target_id}{target_handle_s}"

    # Idempotent: if a connection between the same source output and target
    # input already exists, return it rather than appending a duplicate. We
    # compare structurally (source/target ids + handle name/fieldName) instead
    # of by edge id, since UI-saved edges from older Langflow versions use a
    # different id prefix (`xy-edge__` vs `reactflow__edge-`) even though the
    # underlying connection is the same. A repeat call (batch retry, UI-then-MCP)
    # would otherwise double-wire the flow at runtime.
    for existing in flow["data"]["edges"]:
        if (
            existing.get("source") == source_id
            and existing.get("target") == target_id
            and (existing.get("data") or {}).get("sourceHandle", {}).get("name") == source_output
            and (existing.get("data") or {}).get("targetHandle", {}).get("fieldName") == target_input
        ):
            return existing

    edge = {
        "animated": False,
        "className": "",
        "data": {
            "sourceHandle": source_handle_dict,
            "targetHandle": target_handle_dict,
        },
        "id": edge_id,
        "selected": False,
        "source": source_id,
        "sourceHandle": source_handle_s,
        "target": target_id,
        "targetHandle": target_handle_s,
    }
    flow["data"]["edges"].append(edge)
    return edge