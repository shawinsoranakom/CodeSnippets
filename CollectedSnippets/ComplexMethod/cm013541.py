def guard_or_defer_runtime_assert(
        self, orig_expr: SympyBoolean, msg: str, fx_node: torch.fx.Node | None = None
    ) -> bool:
        """
        Adds a guard that orig_expr is True if we can or fall back to adding an assert
        that is checked at runtime.

        Args:
            orig_expr (sympy.Expr): Boolean expression to assert is true
            msg (str): Message to display on assertion failure
            fx_node (Optional, torch.fx.Node): node in ``self.graph`` corresponding
                to the expression, if applicable
        """
        expr = orig_expr

        # TODO: split conjunctions and evaluate them separately
        # Try to quickly evaluate trivially true/false comparisons
        # using var_to_range, before calling expensive _maybe_evaluate_static.
        fast_result = self._maybe_fast_eval_comparison(expr)
        if fast_result is not None:
            return bool(fast_result)

        if self._should_skip_static_eval(expr):
            new_expr = expr
        else:
            static_expr = self._maybe_evaluate_static(expr)
            if static_expr is not None:
                self.log.debug(
                    "runtime_assert %s == %s [statically known]", orig_expr, static_expr
                )
                # TODO: assert bool(static_expr)
                return bool(static_expr)

            # Attempt to eliminate the unbacked SymInt
            new_expr = self._maybe_evaluate_static(expr, unbacked_only=True)
            if new_expr is None:
                raise AssertionError("new_expr must not be None")
        if (
            not self.prefer_deferred_runtime_asserts_over_guards
            and new_expr.free_symbols <= self.backed_var_to_val.keys()
        ):
            # Do a normal guard
            return self.evaluate_expr(new_expr, fx_node=fx_node)
        # NB: Don't use new_expr as expr; it could contain gunk like shape0
        # which we don't want to guard on

        if (
            self._translation_validation_enabled
            and fx_node is not None
            and not self._suppress_guards_tls()
        ):
            node, fresh = self._create_fx_call_function(torch._assert, (fx_node,))
            if node is None:
                raise AssertionError("node must not be None")
            if fresh:
                self._add_fx_node_metadata(node)

        if not self._suppress_guards_tls():
            self._log_guard("runtime_assert", orig_expr, forcing_spec=False)
            # If you're here because of this assert, read Note [Backwards runtime asserts]
            # in torch/_inductor/graph.py
            if self.runtime_asserts_frozen:
                log.debug("runtime_asserts_frozen but then got %s", expr)
            self._check_frozen(expr, sympy.true)
            # eliminate symbols on equality tests / refine ranges
            self._maybe_guard_rel(expr)

            # canonicalise to remove equations that are trivially equal
            orig_expr = expr
            expr = canonicalize_bool_expr(expr)
            stack = CapturedTraceback.extract(skip=1)
            ra = RuntimeAssert(expr, msg, stack)

            # TODO: Do this in a way that is less janky than int(s.name[1:])
            cands = sorted(
                (s for s in expr.free_symbols if symbol_is_type(s, SymT.UNBACKED_INT)),
                key=lambda s: int(s.name[1:]),
            )
            # Is None when prefer_deferred_runtime_asserts_over_guards=True
            # and the guard in question has no unbacked SymInts in front
            ix = cands[-1] if cands else None
            self.deferred_runtime_asserts.setdefault(ix, []).append(ra)
            self.axioms.update(dict(self.get_implications(self.simplify(expr))))
            self.num_deferred_runtime_asserts += 1
            self._update_version_counter()
        else:
            self._log_guard(
                "runtime_assert [guard suppressed]", orig_expr, forcing_spec=False
            )

        return True