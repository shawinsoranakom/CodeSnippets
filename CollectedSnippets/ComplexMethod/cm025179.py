def compile_policy(
    policy: CategoryType, subcategories: SubCatLookupType, perm_lookup: PermissionLookup
) -> Callable[[str, str], bool]:
    """Compile policy into a function that tests policy.

    Subcategories are mapping key -> lookup function, ordered by highest
    priority first.
    """
    # None, False, empty dict
    if not policy:

        def apply_policy_deny_all(entity_id: str, key: str) -> bool:
            """Decline all."""
            return False

        return apply_policy_deny_all

    if policy is True:

        def apply_policy_allow_all(entity_id: str, key: str) -> bool:
            """Approve all."""
            return True

        return apply_policy_allow_all

    assert isinstance(policy, dict)

    funcs: list[Callable[[str, str], bool | None]] = []

    for key, lookup_func in subcategories.items():
        lookup_value = policy.get(key)

        # If any lookup value is `True`, it will always be positive
        if isinstance(lookup_value, bool):
            return lambda object_id, key: True

        if lookup_value is not None:
            funcs.append(_gen_dict_test_func(perm_lookup, lookup_func, lookup_value))

    if len(funcs) == 1:
        func = funcs[0]

        @wraps(func)
        def apply_policy_func(object_id: str, key: str) -> bool:
            """Apply a single policy function."""
            return func(object_id, key) is True

        return apply_policy_func

    def apply_policy_funcs(object_id: str, key: str) -> bool:
        """Apply several policy functions."""
        for func in funcs:
            if (result := func(object_id, key)) is not None:
                return result
        return False

    return apply_policy_funcs