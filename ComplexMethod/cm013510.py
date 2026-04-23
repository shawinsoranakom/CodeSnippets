def compute_unbacked_bindings(
    shape_env: ShapeEnv | None,
    example_value: object,
    old_example_value: object | None = None,
    peek: bool = False,
) -> dict[sympy.Symbol, pytree.KeyPath] | None:
    """
    After having run fake tensor propagation and producing example_value
    result, traverse example_value looking for freshly bound unbacked
    symbols and record their paths for later.  It is an error if
    we have allocated an unbacked SymInt but it cannot be found in
    example_value.  (NB: this means if you have a multi-output
    function, you must call this on the tuple of tensor output, you
    cannot wait!)

    The peek parameter lets you check out what the bindings are without
    changing the affected list.  This is primarily useful for ensuring
    real_tensor_prop_unbacked_vals is promptly populated when propagate_real_tensors is on.
    """
    if shape_env is None:
        return None

    fresh_sym = shape_env.pending_fresh_unbacked_symbols
    ign_sym = shape_env.ignorable_fresh_unbacked_symbols

    pending = set(fresh_sym)
    ignorable = set(ign_sym)
    if not peek:
        if pending:
            log.info("compute_unbacked_bindings %s", fresh_sym)
        fresh_sym.clear()
        ign_sym.clear()

    if not pending:
        return None

    symbol_to_path = _free_unbacked_symbols_with_path(
        example_value, (), shape_env=shape_env, pending=pending, simplify=False
    )

    pending -= ignorable
    if not peek and pending:
        extra = (
            repr((example_value.stride(), example_value.storage_offset()))
            if isinstance(example_value, torch.Tensor)
            else ""
        )
        msg = (
            f"Pending unbacked symbols {pending} not in returned outputs {example_value} {extra}.\n"
            "Did you accidentally call new_dynamic_size() or item() more times "
            "than you needed to in your fake implementation?\n"
            "For more help, see https://docs.google.com/document/d/1RWrH-3wLEpzR9kCS6gGBNen_-Fs-8PVbWWFE5AcgeWE/edit"
        )
        if torch.fx.experimental._config.soft_pending_unbacked_not_found_error:
            log.warning(msg)
        else:
            raise PendingUnbackedSymbolNotFound(msg)

    # Why do we have to do some rebinding here?  If the original FX node
    # wasn't a binding site because you had a memo hit, but post
    # translation you aren't a memo hit anymore, there's now a new binding
    # site... but we know (because it's the same FX node) that the value
    # is actually the same, they're just not obviously equal anymore.
    #
    # The logic here is written carefully, because unlike the
    # bind_unbacked case, we are not guaranteed to have a symbol for
    # old_sym.  If we have a symbol, do regular rename unbacked to; but if
    # we don't, we need to specially eliminate the fresh unbacked symbol
    # (NB: we are /trusting/ that the memoization is correct, and that we
    # don't need to generate a new runtime assert.  This is load bearing,
    # as repropagation can happen after we've frozen runtime asserts.)
    if old_example_value is not None:
        for keypath in symbol_to_path.values():
            old_sym = pytree.key_get(old_example_value, keypath)
            new_sym = pytree.key_get(example_value, keypath)
            if isinstance(new_sym, SymTypes) and isinstance(
                new_s := new_sym.node.expr, sympy.Symbol
            ):
                if (
                    isinstance(old_sym, SymTypes)
                    and (old_s := old_sym.node.expr) != new_s
                ):
                    # If old_s is not an unbacked_symbol,
                    # we assume that the original unbacked symbol is replaced
                    # by a backed symbol (old_s). This can happen
                    # when this node reuses the original symbol (due to memoi)
                    # and the original symbol gets replaced by the backed symbol.
                    # When this happens we just replace new_s by the old_s
                    # because we know the value is the same.

                    if isinstance(old_s, sympy.Symbol) and free_unbacked_symbols(old_s):
                        shape_env._rename_unbacked_to(new_s, old_s)
                    else:
                        shape_env._eliminate_unbacked(new_s, old_s)
                elif not isinstance(old_sym, SymTypes):
                    shape_env._eliminate_unbacked(new_s, sympy.sympify(old_sym))

    return symbol_to_path