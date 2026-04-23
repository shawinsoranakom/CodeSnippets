def _collect_and_rewrite_defs(node: Any, collected: dict[str, Any]) -> None:
    """Hoist JSON Schema `$defs` into `components.schemas` and rewrite refs.

    Some tooling (like Redoc's sampler) cannot handle JSON Pointer segments
    that contain `$defs`. To keep the schema tool-friendly, we:
    - Collect any `$defs` blocks we find anywhere in the tree.
    - Remove those local `$defs` blocks.
    - Rewrite `"$ref": "#/$defs/Name"` to `"#/components/schemas/Name"`.
    """
    if isinstance(node, dict):
        # Hoist local $defs
        if "$defs" in node and isinstance(node["$defs"], dict):
            for name, schema in node["$defs"].items():
                # Only add if not already present; avoid clobbering explicit components
                collected.setdefault(name, schema)
            node.pop("$defs", None)

        # Rewrite local refs
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.split("/")[-1]
            node["$ref"] = f"#/components/schemas/{name}"

        # Recurse into values
        for value in node.values():
            _collect_and_rewrite_defs(value, collected)

    elif isinstance(node, list):
        for item in node:
            _collect_and_rewrite_defs(item, collected)