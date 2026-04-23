def analyze_value(
    value: Any,
    max_depth: int = 10,
    current_depth: int = 0,
    path: str = "",
    *,
    size_hints: bool = True,
    include_samples: bool = True,
) -> str | dict:
    """Analyze a value and return its structure with additional metadata.

    Args:
        value: The value to analyze
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
        path: Current path in the structure
        size_hints: Whether to include size information for collections
        include_samples: Whether to include sample structure for lists
    """
    if current_depth >= max_depth:
        return f"max_depth_reached(depth={max_depth})"

    try:
        if isinstance(value, list | tuple | set):
            length = len(value)
            if length == 0:
                return "list(unknown)"

            type_info = infer_list_type(list(value))
            size_info = f"[size={length}]" if size_hints else ""

            # For lists of complex objects, include a sample of the structure
            if (
                include_samples
                and length > 0
                and isinstance(value, list | tuple)
                and isinstance(value[0], dict | list)
                and current_depth < max_depth - 1
            ):
                sample = analyze_value(
                    value[0],
                    max_depth,
                    current_depth + 1,
                    f"{path}[0]",
                    size_hints=size_hints,
                    include_samples=include_samples,
                )
                return f"{type_info}{size_info}, sample: {json.dumps(sample)}"

            return f"{type_info}{size_info}"

        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                new_path = f"{path}.{k}" if path else k
                try:
                    result[k] = analyze_value(
                        v,
                        max_depth,
                        current_depth + 1,
                        new_path,
                        size_hints=size_hints,
                        include_samples=include_samples,
                    )
                except Exception as e:  # noqa: BLE001
                    result[k] = f"error({e!s})"
            return result

        return get_type_str(value)

    except Exception as e:  # noqa: BLE001
        return f"error({e!s})"