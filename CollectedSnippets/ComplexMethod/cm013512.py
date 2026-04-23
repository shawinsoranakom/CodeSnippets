def _maybe_evaluate_static_worker(
    expr: _SympyT,
    # NB: this is a tuple to ensure it can be LRU cached
    symbol_info: tuple[_SymbolInfo, ...],
    unbacked_only: bool,
    size_oblivious: bool,
) -> _SympyT | None:
    """
    This variant of ShapeEnv._maybe_evaluate_static has no dependence on
    ShapeEnv and thus can be cached indefinitely.  It does the "heavy" lifting
    for static evaluation, including nontrivial reliance on Sympy simplification
    that occurs when we reallocate the symbols
    """

    # Simplify making use of value range lower bound
    new_shape_env = {}
    new_range_env = {}
    for idx, sinfo in enumerate(symbol_info):
        k, vr, val, is_size_like = sinfo
        if isinstance(val, SingletonInt):
            # Skip var_ranges logic for SingletonInt which is only used
            # for jagged layout NestedTensors today
            continue
        if vr is None:
            raise AssertionError(f"vr must not be None for symbol {k}")
        if size_oblivious and is_size_like:
            lower = max(2, vr.lower)
            # Clamping size-oblivious to some quantity below sys.maxsize
            # helps us determine that f(u0) != sys.maxsize, which is a
            # test that is looking for sys.maxsize as a sentinel, but you
            # don't really want to worry about it for unbacked SymInts.
            # This is similar to the flavor where size oblivious omits
            # 0/1, it changes semantics but in a benign way.
            upper = min(2**48, vr.upper)
            # Excluding the very upper bound can be helpful
            if upper > lower:
                upper = upper - 1
            # This is a bit dodgy: what this means is that there was a
            # size-like unbacked symbol whose upper bound < 2.  This
            # causes... problems.
            if lower <= upper:
                vr = ValueRanges(lower, upper)
        else:
            lower = vr.lower
        # Don't do anything if we don't have a nontrivial lower bound
        # Also don't do anything if we asked only to simplify unbacked
        # SymInt
        if lower is -int_oo or (unbacked_only and val is not None) or not vr.is_int:
            new_range_env[k] = vr
            continue
        # The goal is to take our symbols which have various lower bounds
        # and reallocate them into new symbols which are exactly positive;
        # e.g., if we have s0 in [2, inf], we want to turn it into ess0 in
        # [1, inf], where s0 = ess0 + 1.  This gives the most information
        # to sympy for subsequent simplifications.
        #
        # Positive means >= 1
        # Positive - 1 means >= 0
        # Positive + lower - 1 means >= lower
        # The new symbol 's' is "too low", so when we substitute it in
        # we have to increase it by offset (and conversely, the new
        # variables have to have their value range bounds adjusted as
        # well)
        s = sympy.Symbol(f"evaluate_static_shape_{idx}", positive=True, integer=True)

        # Note:
        #   Offset might be a fraction(e.g. aten.split.Tensor), but shapes are always integers.
        #   Sympy might give unexpected results when comparing an integer with a non-integer
        #   Therefore, we cast offset to int here.
        #   For example:
        #       shape_0 = sympy.Symbol("shape_0", positive=True, integer=True)
        #       expr = sympy.Eq(shape_0 - 1/3, 4)
        #       expr.xreplace({}) # False
        offset = int(lower - 1)
        new_shape_env[k] = s + offset
        new_range_env[s] = SymPyValueRangeAnalysis.add(vr, -offset)

    # TODO: remove this try catch (esp for unbacked_only)
    try:
        # pyrefly: ignore [missing-attribute]
        new_expr = expr.xreplace(new_shape_env)
    except RecursionError:
        log.warning("RecursionError in sympy.xreplace(%s, %s)", expr, new_shape_env)
        return None

    # We need to canonicalize, as after expand we may have something like `a + b = a` and
    # sympy will not simplify the a. The two appearances of the a will then make value ranges
    # analysis give lose bounds
    new_expr = canonicalize_bool_expr(safe_expand(new_expr))
    if new_expr.is_number:
        return new_expr

    # Check if the range can solve it statically
    out = bound_sympy(new_expr, new_range_env)
    if out.is_singleton():
        return out.lower

    return new_expr if unbacked_only else None