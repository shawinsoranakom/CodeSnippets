def _constrain_user_specified_dimhint_range(
    symint: torch.SymInt,
    hint: int,
    dim: _DimHint,
    range_constraints,
    shape_env,
    keypath: KeyPath,
    i: int | None = None,
) -> str | None:
    trace_vr = (
        range_constraints[symint.node.expr]
        if not is_int(symint)
        else ValueRanges(int(symint), int(symint))
    )

    # warn on 0/1 specialization for Dim.AUTO; not an actual error
    if dim.type == _DimHintType.AUTO and trace_vr.is_singleton() and hint in (0, 1):
        pathstr = f"inputs{pytree.keystr(keypath)}"
        if i is not None:
            pathstr += f".shape[{i}]"
        msg = (
            f"dimension {pathstr} 0/1 specialized; Dim.AUTO was specified along "
            + f"with a sample input with hint = {hint}."
        )
        log.warning(msg)

    try:
        user_vr = ValueRanges(
            lower=0 if dim.min is None else dim.min,
            upper=int_oo if dim.max is None else dim.max,
        )
        if is_int(symint):
            out_vr = trace_vr & user_vr
        else:
            range_constraints[symint.node.expr] &= user_vr
            shape_env.var_to_range[symint.node._expr] &= user_vr
            out_vr = range_constraints[symint.node.expr]

        # check for Dim.DYNAMIC specializations; special case error message on 0/1
        if dim.type == _DimHintType.DYNAMIC and out_vr.is_singleton():
            path = f"inputs{pytree.keystr(keypath)}"
            if i is not None:
                path += f".shape[{i}]"
            if (
                trace_vr.is_singleton()
                and hint in (0, 1)
                and not torch.fx.experimental._config.backed_size_oblivious
            ):
                msg = (
                    f"- Received user-specified dim hint Dim.DYNAMIC(min={dim.min}, max={dim.max}), "
                    f"but export 0/1 specialized due to hint of {hint} for dimension {path}."
                )
            else:
                msg = (
                    f"- Received user-specified dim hint Dim.DYNAMIC(min={dim.min}, max={dim.max}), "
                    f"but tracing inferred a static shape of {out_vr.lower} for dimension {path}."
                )
            return msg

    except torch.utils._sympy.value_ranges.ValueRangeError:
        path = f"inputs{pytree.keystr(keypath)}"
        if i is not None:
            path += f".shape[{i}]"
        msg = (
            f"- Received user-specified min/max range of [{dim.min}, {dim.max}], "
            f"conflicting with the inferred min/max range of [{trace_vr.lower}, {trace_vr.upper}], "
            f"for {path}."
        )
        return msg

    return None