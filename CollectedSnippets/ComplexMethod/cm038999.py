def parse_attention_types(node: ast.ClassDef) -> str:
    """Parse supports_attn_type method."""
    method = find_method(node, "supports_attn_type")
    if method is None:
        return "Decoder"

    type_map = {
        "DECODER": "Decoder",
        "ENCODER": "Encoder",
        "ENCODER_ONLY": "Encoder Only",
        "ENCODER_DECODER": "Enc-Dec",
    }
    types: set[str] = set()

    for n in ast.walk(method):
        # Handle `attn_type in (AttentionType.DECODER, ...)`
        if not (
            isinstance(n, ast.Compare)
            and len(n.ops) == 1
            and isinstance(n.ops[0], ast.In)
            and len(n.comparators) == 1
            and isinstance(n.comparators[0], ast.Tuple | ast.Set)
        ):
            continue

        for elt in n.comparators[0].elts:
            if isinstance(elt, ast.Attribute) and elt.attr in type_map:
                types.add(type_map[elt.attr])

    if not types:
        return "Decoder"
    return "All" if types >= set(type_map.values()) else ", ".join(sorted(types))