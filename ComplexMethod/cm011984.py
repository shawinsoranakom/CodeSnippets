def _dynamic_reshape_indexer(
        old_size: Sequence[Expr],
        new_size: Sequence[Expr],
        dense_dim: int | None = None,
    ) -> Callable[[Sequence[Expr]], Sequence[Expr]]:
        """
        Perform a reshape entirely by modifying indexing math
        """
        guard_or_false = V.graph.sizevars.guard_or_false

        def compare_sizes(a: Expr, b: Expr) -> int:
            """
            Compare two symbolic sizes, returning -1 if a < b, 0 if a == b, 1 if a > b.

            For unbacked symbols, guard_or_false returns False, so we fall back
            to divisibility checks.
            """
            if guard_or_false(sympy.Eq(a, b)):
                return 0
            if guard_or_false(sympy.Lt(a, b)):
                return -1
            if guard_or_false(sympy.Gt(a, b)):
                return 1

            # Divisibility fallback for unbacked symbols:
            # e.g. comparing u0 vs u0*u1, statically_known_multiple_of(u0*u1, u0)
            # returns True so we take the merge path (return -1).
            # The merge reindex for old=[u0, u1] -> new=[u0*u1] is:
            #   for k in range(u0 * u1):
            #     i = k // u1
            #     j = k % u1
            #     z[k] = x[i, j] + 1
            # Two cases where this could seem wrong but is still safe:
            #   u1=1: the merge reindex is correct since the extra dim is
            #         size 1 (a no-op). e.g. k // 1 = k, k % 1 = 0.
            #   u0=0: loop is range(0), no kernel runs, result doesn't matter.

            if V.graph.sizevars.statically_known_multiple_of(b, a):
                return -1
            if V.graph.sizevars.statically_known_multiple_of(a, b):
                return 1

            raise GuardOnDataDependentSymNode(sympy.Eq(a, b))

        # TODO: These symbols may not escape, if they don't assert so and
        # treat them as temporary
        vars = [
            sympy_index_symbol_with_prefix(SymT.VIEW, i) for i in range(len(new_size))
        ]

        stack_new = list(zip(vars, new_size))
        stack_old = list(old_size)

        # process the dense dim first
        reordering_dense_dim = (
            dense_dim is not None
            and dense_dim != len(stack_old) - 1
            and len(new_size) == 1
        )
        if reordering_dense_dim:
            assert dense_dim is not None  # mypy
            old_dim = stack_old.pop(dense_dim)
            stack_old.append(old_dim)

        view_expr = []
        while stack_new and stack_old:
            size_old = stack_old.pop()
            var, size_new = stack_new.pop()
            if size_old == 1:
                view_expr.append(sympy.S.Zero)
                stack_new.append((var, size_new))  # re-add
            elif size_new == 1:
                stack_old.append(size_old)  # re-add
            elif compare_sizes(size_new, size_old) == 0:
                view_expr.append(var)
            elif compare_sizes(size_new, size_old) < 0:
                while compare_sizes(size_new, size_old) < 0:
                    var2, size_new2 = stack_new.pop()
                    var = var2 * size_new + var
                    size_new = size_new * size_new2
                view_expr.append(var)
                V.graph.sizevars.check_equals(size_new, size_old)
            elif compare_sizes(size_new, size_old) > 0:
                divisor = sympy.S.One
                modulus = size_old
                view_expr.append(ModularIndexing(var, divisor, modulus))
                divisor = divisor * modulus
                while compare_sizes(size_new, size_old) > 0:
                    modulus = stack_old.pop()
                    view_expr.append(ModularIndexing(var, divisor, modulus))
                    divisor = divisor * modulus
                    size_old = size_old * modulus
                V.graph.sizevars.check_equals(size_new, size_old)
            else:
                raise AssertionError

        while stack_old:
            size_old = stack_old.pop()
            V.graph.sizevars.check_equals(size_old, 1)
            view_expr.append(sympy.S.Zero)

        while stack_new:
            var, size_new = stack_new.pop()
            V.graph.sizevars.check_equals(size_new, 1)

        if dense_dim is not None and len(new_size) == 1:
            view_expr.reverse()
            # Move the last expression (dense dim) to its original position
            dense_expr = view_expr.pop()
            view_expr.insert(dense_dim, dense_expr)
        else:
            view_expr.reverse()

        assert len(view_expr) == len(old_size)

        def reindex(
            index: Sequence[Expr],
        ) -> Sequence[Expr]:
            assert len(index) == len(vars), (len(index), len(vars))
            replacements = dict(zip(vars, index))
            return tuple(sympy_subs(x, replacements) for x in view_expr)

        return reindex