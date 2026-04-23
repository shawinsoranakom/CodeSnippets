def _dispatch_kl(type_p, type_q):
    """
    Find the most specific approximate match, assuming single inheritance.
    """
    matches = [
        (super_p, super_q)
        for super_p, super_q in _KL_REGISTRY
        if issubclass(type_p, super_p) and issubclass(type_q, super_q)
    ]
    if not matches:
        return NotImplemented
    # Check that the left- and right- lexicographic orders agree.
    # mypy isn't smart enough to know that _Match implements __lt__
    # see: https://github.com/python/typing/issues/760#issuecomment-710670503
    left_p, left_q = min(_Match(*m) for m in matches).types  # type: ignore[type-var]
    right_q, right_p = min(_Match(*reversed(m)) for m in matches).types  # type: ignore[type-var]
    left_fun = _KL_REGISTRY[left_p, left_q]
    right_fun = _KL_REGISTRY[right_p, right_q]
    if left_fun is not right_fun:
        warnings.warn(
            f"Ambiguous kl_divergence({type_p.__name__}, {type_q.__name__}). "
            f"Please register_kl({left_p.__name__}, {right_q.__name__})",
            RuntimeWarning,
            stacklevel=2,
        )
    return left_fun