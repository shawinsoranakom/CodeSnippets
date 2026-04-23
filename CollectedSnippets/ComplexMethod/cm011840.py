def compute_slice_index(index, size, default=None):
        if index is None:
            return default

        fn = lambda x: V.graph.sizevars.guard_or_false(x)  # noqa: E731
        index = sympy.expand(index)
        size = sympy.expand(size)
        if fn(sympy.And(sympy.Ge(index, 0), sympy.Le(index, size))):
            return index
        elif fn(sympy.And(sympy.Lt(index, 0), sympy.Ge(index, -size))):
            return index + size
        elif fn(sympy.Gt(index, size)):
            return size
        elif fn(sympy.Lt(index, -size)):
            return 0
        elif fn(sympy.Ge(index, 0)):
            # If index >= 0, the resolved index is at most min(index, size).
            return sympy.Min(index, size)
        elif fn(sympy.Lt(index, 0)):
            # If index < 0, wrap and clamp: the resolved index is at least 0.
            return sympy.Max(index + size, 0)
        return None