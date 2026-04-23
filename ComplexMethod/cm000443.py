def parse_execution_output(
    output_item: tuple[str, Any],
    link_output_selector: str,
    sink_node_id: str | None = None,
    sink_pin_name: str | None = None,
) -> Any:
    """
    Retrieve a nested value out of `output` using the flattened `link_output_selector`.

    On any failure (wrong name, wrong type, out-of-range, bad path) returns **None**.

    ### Special Case: Tool pins
    For regular output pins, the `output_item`'s name will simply be the field name, and
    `link_output_selector` (= the `source_name` of the link) may provide a "selector"
    used to extract part of the output value and route it through the link
    to the next node.

    However, for tool pins, it is the other way around: the `output_item`'s name
    provides the routing information (`tools_^_{sink_node_id}_~_{field_name}`),
    and the `link_output_selector` is simply `"tools"`
    (or `"tools_^_{tool_name}_~_{field_name}"` for backward compatibility).

    Args:
        output_item: Tuple of (base_name, data) representing a block output entry.
        link_output_selector: The flattened field name to extract from the output data.
        sink_node_id: Sink node ID, used for tool use routing.
        sink_pin_name: Sink pin name, used for tool use routing.

    Returns:
        The value at the specified path, or `None` if not found/invalid.
    """
    output_pin_name, data = output_item

    # Special handling for tool pins
    if is_tool_pin(link_output_selector) and (  # "tools" or "tools_^_…"
        output_pin_name.startswith("tools_^_") and "_~_" in output_pin_name
    ):
        if not (sink_node_id and sink_pin_name):
            raise ValueError(
                "sink_node_id and sink_pin_name must be provided for tool pin routing"
            )

        # Extract routing information from emit key: tools_^_{node_id}_~_{field}
        selector = output_pin_name[8:]  # Remove "tools_^_" prefix
        target_node_id, target_input_pin = selector.split("_~_", 1)
        if target_node_id == sink_node_id and target_input_pin == sink_pin_name:
            return data
        else:
            return None

    # Exact match → whole object
    if link_output_selector == output_pin_name:
        return data

    # Must start with the expected name
    if not link_output_selector.startswith(output_pin_name):
        return None
    path = link_output_selector[len(output_pin_name) :]
    if not path:
        return None  # nothing left to parse

    tokens = _tokenise(path)
    if tokens is None:
        return None

    cur: Any = data
    for delim, ident in tokens:
        if delim == LIST_SPLIT:
            # list[index]
            try:
                idx = int(ident)
            except ValueError:
                return None
            if not isinstance(cur, list) or idx >= len(cur):
                return None
            cur = cur[idx]

        elif delim == DICT_SPLIT:
            if not isinstance(cur, dict) or ident not in cur:
                return None
            cur = cur[ident]

        elif delim == OBJC_SPLIT:
            if not hasattr(cur, ident):
                return None
            cur = getattr(cur, ident)

        else:
            return None  # unreachable

    return cur