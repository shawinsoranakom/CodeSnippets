def issubtype(left, right, recursive=True):
    r"""
    Check if the left-side type is a subtype of the right-side type.

    If any of type is a composite type like `Union` and `TypeVar` with
    bounds, it would be expanded into a list of types and check all
    of left-side types are subtypes of either one from right-side types.
    """
    left = TYPE2ABC.get(left, left)
    right = TYPE2ABC.get(right, right)

    if right is Any or left == right:
        return True

    if isinstance(right, _GenericAlias):
        if getattr(right, "__origin__", None) is Generic:
            return True

    if right is type(None):
        return False

    # Right-side type
    constraints = _decompose_type(right)

    if len(constraints) == 0 or Any in constraints:
        return True

    if left is Any:
        return False

    # Left-side type
    variants = _decompose_type(left)

    # all() will return True for empty variants
    if len(variants) == 0:
        return False

    return all(
        _issubtype_with_constraints(variant, constraints, recursive)
        for variant in variants
    )