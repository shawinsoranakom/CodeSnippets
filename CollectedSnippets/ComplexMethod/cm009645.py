def merge_dicts(left: dict[str, Any], *others: dict[str, Any]) -> dict[str, Any]:
    r"""Merge dictionaries.

    Merge many dicts, handling specific scenarios where a key exists in both
    dictionaries but has a value of `None` in `'left'`. In such cases, the method uses
    the value from `'right'` for that key in the merged dictionary.

    Args:
        left: The first dictionary to merge.
        others: The other dictionaries to merge.

    Returns:
        The merged dictionary.

    Raises:
        TypeError: If the key exists in both dictionaries but has a different type.
        TypeError: If the value has an unsupported type.

    Example:
        If `left = {"function_call": {"arguments": None}}` and
        `right = {"function_call": {"arguments": "{\n"}}`, then, after merging, for the
        key `'function_call'`, the value from `'right'` is used, resulting in
        `merged = {"function_call": {"arguments": "{\n"}}`.
    """
    merged = left.copy()
    for right in others:
        for right_k, right_v in right.items():
            if right_k not in merged or (
                right_v is not None and merged[right_k] is None
            ):
                merged[right_k] = right_v
            elif right_v is None:
                continue
            elif type(merged[right_k]) is not type(right_v):
                msg = (
                    f'additional_kwargs["{right_k}"] already exists in this message,'
                    " but with a different type."
                )
                raise TypeError(msg)
            elif isinstance(merged[right_k], str):
                # TODO: Add below special handling for 'type' key in 0.3 and remove
                # merge_lists 'type' logic.
                #
                # if right_k == "type":
                #     if merged[right_k] == right_v:
                #         continue
                #     else:
                #         raise ValueError(
                #             "Unable to merge. Two different values seen for special "
                #             f"key 'type': {merged[right_k]} and {right_v}. 'type' "
                #             "should either occur once or have the same value across "
                #             "all dicts."
                #         )
                if (right_k == "index" and merged[right_k].startswith("lc_")) or (
                    right_k in {"id", "output_version", "model_provider"}
                    and merged[right_k] == right_v
                ):
                    continue
                merged[right_k] += right_v
            elif isinstance(merged[right_k], dict):
                merged[right_k] = merge_dicts(merged[right_k], right_v)
            elif isinstance(merged[right_k], list):
                merged[right_k] = merge_lists(merged[right_k], right_v)
            elif merged[right_k] == right_v:
                continue
            elif isinstance(merged[right_k], int):
                # Preserve identification and temporal fields using last-wins strategy
                # instead of summing:
                # - index: identifies which tool call a chunk belongs to
                # - created/timestamp: temporal values that shouldn't be accumulated
                if right_k in {"index", "created", "timestamp"}:
                    merged[right_k] = right_v
                else:
                    merged[right_k] += right_v
            else:
                msg = (
                    f"Additional kwargs key {right_k} already exists in left dict and "
                    f"value has unsupported type {type(merged[right_k])}."
                )
                raise TypeError(msg)
    return merged