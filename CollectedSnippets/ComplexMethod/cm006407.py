def _expand_node(
    compact_node: CompactNode,
    flat_components: dict[str, Any],
) -> dict[str, Any]:
    """Expand a compact node to full node format.

    Args:
        compact_node: The compact node to expand
        flat_components: Flattened component templates dict

    Returns:
        Full node data structure

    Raises:
        ValueError: If component type is not found and node is not edited
    """
    # If the node is edited, it should have full node data
    if compact_node.edited:
        if not compact_node.node:
            msg = f"Node {compact_node.id} is marked as edited but has no node data"
            raise ValueError(msg)
        return {
            "id": compact_node.id,
            "type": "genericNode",
            "data": {
                "type": compact_node.type,
                "node": compact_node.node,
                "id": compact_node.id,
            },
        }

    # Look up component template
    if compact_node.type not in flat_components:
        msg = f"Component type '{compact_node.type}' not found in component index"
        raise ValueError(msg)

    # Fast deepcopy for known structure.
    # Instead of deepcopy, use shallow copy and per-field dict copy for template subdict.
    src_data = flat_components[compact_node.type]
    # Assume template is a dict (if present)
    if "template" in src_data:
        # Shallow copy for outer structure
        template_data = src_data.copy()
        # Deep copy only 'template' portion (which is mutated and thus not shared)
        template_data["template"] = template = src_data["template"].copy()
    else:
        template_data = src_data.copy()
        template = template_data.get("template", {})

    # Merge user values into template
    # Use items() directly, reduce field lookups
    for field_name, field_value in compact_node.values.items():
        t_value = template.get(field_name)
        if t_value is not None:
            if isinstance(t_value, dict):
                t_value["value"] = field_value
            else:
                template[field_name] = field_value
        else:
            # Add as new field if not in template
            template[field_name] = {"value": field_value}

    return {
        "id": compact_node.id,
        "type": "genericNode",
        "data": {
            "type": compact_node.type,
            "node": template_data,
            "id": compact_node.id,
        },
    }