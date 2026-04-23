def _is_valid_type(
    expected_type: list[str] | str | None | object,
    node: nodes.NodeNG,
    in_return: bool = False,
) -> bool:
    """Check the argument node against the expected type."""
    if expected_type is _Special.UNDEFINED:
        return True

    if isinstance(expected_type, list):
        for expected_type_item in expected_type:
            if _is_valid_type(expected_type_item, node, in_return):
                return True
        return False

    # Const occurs when the type is None
    if expected_type is None or expected_type == "None":
        return isinstance(node, nodes.Const) and node.value is None

    assert isinstance(expected_type, str)

    # Const occurs when the type is an Ellipsis
    if expected_type == "...":
        return isinstance(node, nodes.Const) and node.value == Ellipsis

    # Special case for an empty list, such as Callable[[], TestServer]
    if expected_type == "[]":
        return isinstance(node, nodes.List) and not node.elts

    # Special case for `xxx | yyy`
    if match := _TYPE_HINT_MATCHERS["a_or_b"].match(expected_type):
        return (
            isinstance(node, nodes.BinOp)
            and _is_valid_type(match.group(1), node.left)
            and _is_valid_type(match.group(2), node.right)
        )

    # Special case for `xxx[aaa, bbb, ccc, ...]
    if (
        isinstance(node, nodes.Subscript)
        and isinstance(node.slice, nodes.Tuple)
        and (
            match := _TYPE_HINT_MATCHERS[f"x_of_y_{len(node.slice.elts)}"].match(
                expected_type
            )
        )
    ):
        # This special case is separate because we want Mapping[str, Any]
        # to also match dict[str, int] and similar
        if (
            len(node.slice.elts) == 2
            and in_return
            and match.group(1) == "Mapping"
            and match.group(3) == "Any"
        ):
            return (
                isinstance(node.value, nodes.Name)
                # We accept dict when Mapping is needed
                and node.value.name in ("Mapping", "dict")
                and isinstance(node.slice, nodes.Tuple)
                and _is_valid_type(match.group(2), node.slice.elts[0])
                # Ignore second item
                # and _is_valid_type(match.group(3), node.slice.elts[1])
            )

        # This is the default case
        return (
            _is_valid_type(match.group(1), node.value)
            and isinstance(node.slice, nodes.Tuple)
            and all(
                _is_valid_type(match.group(n + 2), node.slice.elts[n], in_return)
                for n in range(len(node.slice.elts))
            )
        )

    # Special case for xxx[yyy]
    if match := _TYPE_HINT_MATCHERS["x_of_y_1"].match(expected_type):
        return (
            isinstance(node, nodes.Subscript)
            and _is_valid_type(match.group(1), node.value)
            and _is_valid_type(match.group(2), node.slice)
        )

    # Special case for float in return type
    if (
        expected_type == "float"
        and in_return
        and isinstance(node, nodes.Name)
        and node.name in ("float", "int")
    ):
        return True

    # Special case for int in argument type
    if (
        expected_type == "int"
        and not in_return
        and isinstance(node, nodes.Name)
        and node.name in ("float", "int")
    ):
        return True

    # Allow subscripts or type aliases for generic types
    if (
        isinstance(node, nodes.Subscript)
        and isinstance(node.value, nodes.Name)
        and node.value.name in _KNOWN_GENERIC_TYPES
    ) or (
        isinstance(node, nodes.Name) and node.name.endswith(_KNOWN_GENERIC_TYPES_TUPLE)
    ):
        return True

    # Name occurs when a namespace is not used, eg. "HomeAssistant"
    if isinstance(node, nodes.Name) and node.name == expected_type:
        return True

    # Attribute occurs when a namespace is used, eg. "core.HomeAssistant"
    return isinstance(node, nodes.Attribute) and (
        node.attrname == expected_type or node.as_string() == expected_type
    )