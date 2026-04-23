def build_param_list(ctx, py_args, self_name, pdt_arg_types=None):
    if py_args.kwarg is not None:
        expr = py_args.kwarg
        ctx_range = ctx.make_range(
            expr.lineno, expr.col_offset - 1, expr.col_offset + len(expr.arg)
        )
        raise NotSupportedError(ctx_range, _vararg_kwarg_err)
    if py_args.vararg is not None:
        expr = py_args.vararg
        ctx_range = ctx.make_range(
            expr.lineno, expr.col_offset - 1, expr.col_offset + len(expr.arg)
        )
        raise NotSupportedError(ctx_range, _vararg_kwarg_err)
    if len(py_args.kw_defaults) > 0:
        # kw_defaults is a list of the values for the kwargs (which default to None),
        # so they don't actually have line numbers.
        for arg in py_args.kw_defaults:
            if arg is not None:
                ctx_range = build_expr(ctx, arg).range()
                raise NotSupportedError(ctx_range, _vararg_kwarg_err)

    # List of Tuple of args and type as inferred by profile directed typing
    arg_and_types = [
        (
            arg,
            pdt_arg_types[arg.arg]
            if pdt_arg_types and bool(pdt_arg_types[arg.arg])
            else None,
        )
        for arg in py_args.args
    ]
    arg_and_types_kwonlyargs = [
        (
            arg,
            pdt_arg_types[arg.arg]
            if pdt_arg_types and bool(pdt_arg_types[arg.arg])
            else None,
        )
        for arg in py_args.kwonlyargs
    ]

    result = [
        build_param(ctx, arg, self_name, kwarg_only=False, pdt_arg_type=arg_type)
        for arg, arg_type in arg_and_types
    ]
    result += [
        build_param(ctx, arg, self_name, kwarg_only=True, pdt_arg_type=arg_type)
        for arg, arg_type in arg_and_types_kwonlyargs
    ]
    return result