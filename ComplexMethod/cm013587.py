def add_runtime_asserts(ras: list[RuntimeAssert]) -> None:
        for ra in ras:
            if (
                # redundant
                ra.expr in added_asserts
                # if we've already added a constrain_range call for this symbol,
                # then single-symbol bound asserts like u0 >= 0, u0 <= 5 are redundant.
                or (
                    len(ra.expr.free_symbols) == 1
                    and next(iter(ra.expr.free_symbols)) in constrained_unbacked_symbols
                    and _is_bound_expr_for_symbol(ra.expr)
                )
                # don't try to reify sympy functions we can't turn into FX nodes
                or _has_uninterpretable_sympy_function(ra.expr)
            ):
                continue

            log.debug("inserting runtime assert %s", ra.expr)
            # Need to process ALL free symbols, not just unbacked ones
            fvs = free_symbols(ra.expr)
            missing = fvs - expr_to_proxy.keys()
            if missing:
                i1 = min(missing, key=str)
                # TODO: Remove relaxing assert on unbacked_symint https://github.com/pytorch/pytorch/issues/119689
                # assert shape_env.is_unbacked_symint(i1), i1
                ras_by_symbol.setdefault(i1, []).append(ra)
            else:
                # Convert the sympy expression into a sequence of FX
                # nodes
                with _set_node_metadata_hook(
                    gm,
                    functools.partial(
                        _node_metadata_hook,
                        stack_trace=node.meta.get("stack_trace"),
                        nn_module_stack=node.meta.get("nn_module_stack"),
                        # nodes added in `apply_runtime_assertion_pass` will have the same annotation
                        # as the input node to the assertion
                        custom=node.meta.get("custom"),
                    ),
                ):
                    res = _sympy_interp(expr_to_proxy, ra.expr).node

                    graph.call_function(
                        torch.ops.aten._assert_scalar.default,
                        # TODO: use ra.msg here, but it's pretty
                        # useless right now
                        (
                            res,
                            f"Runtime assertion failed for expression {ra.expr} on node '{res}'",
                        ),
                    )
                added_asserts.add(ra.expr)