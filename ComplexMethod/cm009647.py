def merge_obj(left: Any, right: Any) -> Any:
    """Merge two objects.

    It handles specific scenarios where a key exists in both dictionaries but has a
    value of `None` in `'left'`. In such cases, the method uses the value from `'right'`
    for that key in the merged dictionary.

    Args:
        left: The first object to merge.
        right: The other object to merge.

    Returns:
        The merged object.

    Raises:
        TypeError: If the key exists in both dictionaries but has a different type.
        ValueError: If the two objects cannot be merged.
    """
    if left is None or right is None:
        return left if left is not None else right
    if type(left) is not type(right):
        msg = (
            f"left and right are of different types. Left type:  {type(left)}. Right "
            f"type: {type(right)}."
        )
        raise TypeError(msg)
    if isinstance(left, str):
        return left + right
    if isinstance(left, dict):
        return merge_dicts(left, right)
    if isinstance(left, list):
        return merge_lists(left, right)
    if left == right:
        return left
    msg = (
        f"Unable to merge {left=} and {right=}. Both must be of type str, dict, or "
        f"list, or else be two equal objects."
    )
    raise ValueError(msg)