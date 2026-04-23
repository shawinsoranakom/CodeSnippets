def _apply_tweaks(flow_dict: dict[str, Any], tweaks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Return a *deep copy* of *flow_dict* with template field values patched.

    *tweaks* maps a node identifier -- one of the node's ``id``, ``data.type``,
    or ``display_name`` -- to a ``{field_name: new_value}`` dict.  All nodes
    whose identifier matches a tweak key are updated.
    """
    flow = copy.deepcopy(flow_dict)
    nodes = flow.get("data", {}).get("nodes", [])
    for node in nodes:
        node_data: dict = node.get("data") or {}
        node_id: str = node.get("id", "")
        node_type: str = node_data.get("type", "")
        node_obj: dict = node_data.get("node") or {}
        display_name: str = node_obj.get("display_name", "")
        template: dict = node_obj.get("template") or {}

        for tweak_key, field_overrides in tweaks.items():
            if tweak_key not in (node_id, node_type, display_name):
                continue
            for fname, fvalue in field_overrides.items():
                if fname not in template:
                    continue
                if isinstance(template[fname], dict):
                    template[fname]["value"] = fvalue
                else:
                    template[fname] = fvalue
    return flow