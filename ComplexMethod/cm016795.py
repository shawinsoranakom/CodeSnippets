def normalize_outputs(outputs: dict) -> dict:
    """Normalize raw node outputs for the jobs API.

    Transforms string 3D filenames into file output dicts and removes
    None items. All other items (non-3D strings, dicts, etc.) are
    preserved as-is.
    """
    normalized = {}
    for node_id, node_outputs in outputs.items():
        if not isinstance(node_outputs, dict):
            normalized[node_id] = node_outputs
            continue
        normalized_node = {}
        for media_type, items in node_outputs.items():
            if media_type == 'animated' or not isinstance(items, list):
                normalized_node[media_type] = items
                continue
            normalized_items = []
            for item in items:
                if item is None:
                    continue
                norm = normalize_output_item(item)
                normalized_items.append(norm if norm is not None else item)
            normalized_node[media_type] = normalized_items
        normalized[node_id] = normalized_node
    return normalized