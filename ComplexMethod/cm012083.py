def canonicalize(
        self, index: sympy.Expr
    ) -> tuple[sympy.Expr, tuple[sympy.Symbol, ...], tuple[sympy.Expr, ...]]:
        if not self._should_normalize:
            sizes = [V.graph.sizevars.simplify(x) for x in self._var_ranges.values()]
            var_names = [k for k, v in zip(self._var_ranges.keys(), sizes) if v != 1]
            sizes = [v for v in sizes if v != 1]

            self.drop_unused_symbols(index, var_names, sizes)

            return index, tuple(var_names), tuple(sizes)  # type: ignore[return-value, arg-type]
        var_ranges = {
            k: V.graph.sizevars.simplify(v)
            for k, v in self._var_ranges.items()
            # TODO(jansel): explore this further normalization
            # if k in free_symbols
        }
        return self._normalize(index, var_ranges)