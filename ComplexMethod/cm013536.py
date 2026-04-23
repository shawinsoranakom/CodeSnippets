def _maybe_guard_rel(self, expr: sympy.Expr) -> None:
        """
        The relational guard is guarded to be true.  Use this information to
        simplify shapes (i.e. a == b or a % 5 == 0)
        """
        if isinstance(expr, sympy.And):
            for arg in expr.args:
                self._maybe_guard_rel(arg)
            return
        elif not isinstance(expr, sympy.Rel):
            return

        # A good example of what goes wrong if you don't do this is
        # python test/functorch/test_aotdispatch.py -k
        # test_aot_autograd_symbolic_module_exhaustive_nn_LazyConv3d_cpu_float32
        if isinstance(expr, sympy.Ne):
            return

        free = list(expr.free_symbols)

        if len(free) == 0:
            raise AssertionError(
                f"The expression should not be static by this point: {expr}"
            )
        # In case of really gnarly expression, we don't blow up
        if len(free) > 5:
            return

        # Prioritize unbacked symints for solving by ordering them last.
        # Prefer to simplify out lexicographically higher symbols (i.e. simplify out s4 over s3).
        #   (NB: this unfortunately isn't strictly equivalent to simplifying out newer symbols)
        # Prefer to simplify out symbols with ephemeral sources.
        def _smart_symbol_sort(x: sympy.Symbol) -> tuple[int, int, str]:
            has_only_ephemeral_sources = x in self.var_to_sources and all(
                s.is_ephemeral() for s in self.var_to_sources[x]
            )

            hint = self.backed_var_to_val.get(x)
            if hint is None or isinstance(hint, SingletonInt):
                # NB: size_hint is int, not sympy.Expr, do not use int_oo here.
                # SingletonInt is used to represent jagged/nested tensor dimensions
                # (e.g. the irregular ragged dimension). It cannot be converted to
                # int, so we treat it the same as an unknown size. This matches the
                # behavior of size_hint(), which returns None for SingletonInt.
                size = sys.maxsize
            elif symbol_is_type(x, SymT.SIZE):
                size = int(hint)
            else:
                size = sys.maxsize
            name = x.name
            # 1 puts ephemeral sourced symbols first when sorting in reverse
            return (1 if has_only_ephemeral_sources else 0, size, name)

        free = sorted(free, key=_smart_symbol_sort, reverse=True)  # type: ignore[attr-defined]
        lhs = expr.lhs
        rhs = expr.rhs

        self._refine_ranges(expr)

        # The rest of this stuff is for equality only
        if not isinstance(expr, sympy.Eq):
            return

        if not expr.has(Mod):
            try:
                floor_div_atoms = lhs.atoms(FloorDiv).union(rhs.atoms(FloorDiv))
                if len(floor_div_atoms) > 0 and any(
                    a.divisor != 1 for a in floor_div_atoms
                ):
                    raise NotImplementedError

                # Never replace unbacked symbols with other unbacked symbols that are
                # not function arguments. (ex:mark_unbacked symbols are fine to replace
                # other unbacked, but not those coming from .item() calls).

                # This is error prone because you can cause references to
                # unbacked symbols to time travel backwards.  E.g.,
                #
                # u1 = x.item()
                # ... use of u1 ...
                # u2 = y.item()
                # u3 = z.item()
                # torch._check(u1 == u2 + u3)
                #
                # If you replace u1 with u2 + u3, then the use of u1 now
                # references u2 and u3 prior to them actually being bound at
                # runtime.  It's pretty inconvenient to setup control
                # dependencies for substitutions, so ban it entirely.
                def trivial_solve(lhs: sympy.Expr, rhs: sympy.Expr) -> bool:
                    if isinstance(lhs, sympy.Symbol):
                        if free_unbacked_symbols(
                            lhs
                        ) and not _free_non_source_unbacked_symbols(
                            rhs, self.unbacked_inputs
                        ):
                            return True
                        if symbol_is_type(lhs, SymT.FLOAT):
                            return True
                        # TODO: Maybe trivial solutions for int should also be
                        # done?
                    return False

                # short-circuit when no solving is needed
                if trivial_solve(lhs, rhs):
                    self._set_replacement(lhs, self._find(rhs), "trivial_lhs")
                elif trivial_solve(rhs, lhs):
                    self._set_replacement(rhs, self._find(lhs), "trivial_rhs")
                else:
                    r = try_solve(expr, free[0], floordiv_inequality=False)
                    if r is not None and all(
                        t.is_integer for t in sympy.preorder_traversal(r[1])
                    ):
                        new_var = self._find(r[1])
                        ok = len(free_unbacked_symbols(new_var)) == 0
                        if ok:
                            self._set_replacement(free[0], new_var, "solve")

            except NotImplementedError:
                pass
        else:
            # expression has mod.
            mod_expr = next(iter(expr.atoms(Mod)))
            try:
                r = try_solve(expr, mod_expr, floordiv_inequality=False)
                if r is not None and r[1] == 0:
                    self._add_divisible(mod_expr)
            except NotImplementedError:
                pass
        return