def _check_symint(
    symint: int | torch.SymInt,
    arg: int,
    range_constraints,
    unification_map,
    keypath: KeyPath,
    i: int | None = None,
) -> None:
    from torch.export.dynamic_shapes import _IntWrapper

    if (
        isinstance(arg, torch.SymInt)
        and not arg.node.expr.is_number
        or isinstance(arg, _IntWrapper)
    ):
        # This can happen when, say, arg is a fake tensor.
        # We do not run checks on symbolic shapes of fake inputs as
        # such checks can affect the shape env.
        return

    import sympy

    from torch._export.passes.add_runtime_assertions_for_constraints_pass import (
        _convert_range_to_int,
    )
    from torch.utils._sympy.solve import try_solve

    if isinstance(symint, torch.SymInt) and len(symint.node.expr.free_symbols) == 1:
        symbol = next(iter(symint.node.expr.free_symbols))
        if symbol in unification_map:
            existing_dim = symint.node.expr.subs(unification_map)
            if arg != existing_dim:
                path = get_keystr(keypath)
                if i is not None:
                    path += f".shape[{i}]"
                raise RuntimeError(
                    f"Expected input at {path} to be equal to {existing_dim}, but got {arg}",
                )
        else:
            if isinstance(symint.node.expr, sympy.Symbol):
                # Short cut for try_solve below. Also useful in cases where
                # sympy.Eq(symint.node.expr, arg) would evaluate to False
                # purely because symbol is constrained to be size-like,
                # e.g., when symint.node.expr = symbol and arg = 0.
                unification_map[symbol] = int(arg)
            else:
                solution = try_solve(sympy.Eq(symint.node.expr, arg), symbol)
                if solution is None:
                    path = get_keystr(keypath)
                    if i is not None:
                        path += f".shape[{i}]"
                    raise RuntimeError(
                        f"Expected input {path} = {arg} to be "
                        f"of the form {symint.node.expr}, where {symbol} is an integer"
                    )
                else:
                    unification_map[symbol] = int(solution[1])

        if symint.node.expr in range_constraints:
            min_val, max_val = _convert_range_to_int(
                range_constraints[symint.node.expr]
            )
            # NOTE: we allow dimensions to be 0/1 at runtime
            if min_val > 2:
                if arg < min_val:
                    path = get_keystr(keypath)
                    if i is not None:
                        path += f".shape[{i}]"
                    raise RuntimeError(
                        f"Expected input at {path} to be >= {min_val}, but got {arg}",
                    )
            if max_val < math.inf:
                if arg > max_val:
                    path = get_keystr(keypath)
                    if i is not None:
                        path += f".shape[{i}]"
                    raise RuntimeError(
                        f"Expected input at {path} to be <= {max_val}, but got {arg}",
                    )
    elif isinstance(symint, torch.SymInt) and not symint.node.expr.is_number:
        # this means we deferred a guard from export analysis to runtime, let this pass
        # we'll add a runtime assert checking equality to this replacement expression
        pass
    elif arg != int(symint):
        path = get_keystr(keypath)
        if i is not None:
            path += f".shape[{i}]"
        raise RuntimeError(
            f"Expected input at {path} to be equal to {symint}, but got {arg}. "
            "If you meant for this dimension to be dynamic, please re-export and specify dynamic_shapes "
            "(e.g. with Dim.DYNAMIC)"
        )