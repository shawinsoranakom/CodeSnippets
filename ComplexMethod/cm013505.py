def rebind_unbacked(
    shape_env: ShapeEnv | None, n: torch.fx.Node, result: Result
) -> None:
    """
    Suppose we are retracing a pre-existing FX graph that previously had
    fake tensor propagation (and therefore unbacked SymInts).  When we retrace,
    we re-propagate fake tensors, which results in new unbacked SymInts.
    When this happens, we need to tell the shape environment about the equivalence
    of the old and new unbacked SymInts.  Pass us the old torch.fx.Node (which
    has the old binding information) and the new result (which we can extract the
    new unbacked SymInts out from).
    """

    # Inputs never need rebinding
    if n.op == "placeholder":
        return

    if bindings := resolve_unbacked_bindings(
        shape_env, n.meta.get("unbacked_bindings")
    ):
        if shape_env is None:
            raise AssertionError("shape_env should not be None")
        for raw_u0, path in bindings.items():
            u1 = pytree.key_get(result, path)

            # Sometimes, things were previously unbacked bindings become constants.
            # There are two situations this can happen.
            #
            # First, you might have a runtime assert that causes the
            # constant-ification.  In this case, the /binding/ itself will
            # still be an unbacked symbol (because we will only force it
            # to be a constant later in fake tensor propagation).  In this
            # case, u1 is a SymInt and we still do all our work as normal.
            #
            # But second, it might be that fake tensor propagation DIRECTLY
            # converted the unbacked SymInt into a constant.  This happens
            # more rarely, but we have identified two situations it can
            # validly occur:
            #
            # - If you have a tensor_version operator, these are initially
            #   allocated as unbacked SymInts, but after AOTAutograd they
            #   get forced specialized to specific values.  In this case,
            #   there is no reason to do runtime asserts on them, this is
            #   just a hack to properly keep track of them to start.
            #
            # - If you have an item() call on a constant tensor, the result
            #   of the item() call is constant and we do not need runtime
            #   asserts on this symbol.  In
            #   https://github.com/pytorch/pytorch/issues/140625 we have a
            #   case where in the initial trace of the program we are unable
            #   to determine that torch.tensor is constant, but then
            #   subsequent passes cause torch.tensor to become a constant and
            #   then the unbacked symbol goes poof.
            #
            # In all of these cases, it is no longer necessary to generate
            # deferred runtime asserts, since other subsystems (e.g., the
            # constant-ification pass) ensure that the quantity is now truly
            # static and cannot change at runtime.  So it's OK to discard
            # in these situations.
            #
            # There is one more hazard (re
            # https://github.com/pytorch/pytorch/issues/141248), the problem
            # is that you can end up with "dangling" unbacked symbols that
            # exist in the ShapeEnv but are never bound anywhere.  You might
            # like an invariant that unbacked symbols never get lost.  But
            # we do not have this invariant, so do not try to enforce it.
            if isinstance(u1, (int, float)):
                log.info(
                    "rebind_unbacked: discard %s %s %s -> %s",
                    n.target,
                    raw_u0,
                    path,
                    u1,
                )
                continue

            # We only care about rebinding unbacked things
            if u1.node.hint is not None:
                continue

            # unbacked symbols bindings might be replaced to other backed or
            # unbacked replacements.
            #
            # Example:
            #   u = x.item()
            #   torch._check(u == 5)
            #
            # The safest approach is to retrieve raw_u1 from u1.node._expr
            # and perform the rebinding on the original unbacked symbol,
            # even if it’s no longer directly referenced.
            #
            # In other words, we should always rebind the original symbol
            # before any replacements are applied.
            #   u0 -> u0 == s1
            raw_u1 = u1.node._expr

            # TODO Do we still need this logic below?
            # Simplify SymBool binding
            if (
                isinstance(raw_u1, sympy.Piecewise)
                and len(raw_u1.args) == 2
                and (
                    raw_u1_args0 := cast(
                        tuple[sympy.Basic, sympy.Basic], raw_u1.args[0]
                    )
                )
                and raw_u1_args0[0] == 1
                and isinstance(eq := raw_u1_args0[1], sympy.Eq)
                and isinstance(new_raw_u1 := eq.lhs, sympy.Symbol)
                and shape_env.var_to_range[new_raw_u1].issubset(ValueRanges(0, 1))
                and eq.rhs == 1
                and cast(tuple[sympy.Basic, sympy.Basic], raw_u1.args[1]) == (0, True)
            ):
                # This is what the pattern match above is testing
                repacked = _sympy_cast_symbool_to_symint_guardless(
                    sympy.Eq(new_raw_u1, 1)
                )
                if repacked != raw_u1:
                    raise AssertionError(f"{repacked} != {raw_u1}")
                # Cancel the to_int(to_bool(x)). This is sound because x in
                # [0, 1]

                raw_u1 = new_raw_u1

            if not isinstance(raw_u1, sympy.Symbol):
                if raw_u1.free_symbols:
                    raise AssertionError(f"should have been constant, but got {raw_u1}")
                continue

            # The old and new could be the same if you improperly hit the memo
            # while retracing.  Make sure you updated FakeTensorMode.epoch
            if raw_u0 == raw_u1:
                raise AssertionError(f"{raw_u0} possible memo disaster")
            # Reuse the OLD symbol name
            shape_env._rename_unbacked_to(raw_u1, raw_u0)