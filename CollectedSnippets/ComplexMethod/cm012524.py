def _detect_iter_scatter(
        self, index: sympy.Expr, indirect_var: str, indirect_coeff: int
    ) -> dict[str, Any] | None:
        """Detect scatter pattern with iteration variables."""
        used_iter_vars = self._get_used_iter_vars(index)

        # Collect (var_name, coefficient, length) for each variable
        all_vars: list[tuple[str, int, int]] = []
        for var in used_iter_vars:
            coeff = int(self._get_index_coefficient(index, var))
            if coeff > 0 and var in self.range_tree_nodes:
                length = self._safe_int(self.range_tree_nodes[var].length)
                if length is None:
                    return None
                all_vars.append((str(var), coeff, length))

        all_vars.append((indirect_var, indirect_coeff, -1))
        all_vars.sort(key=lambda x: x[1], reverse=True)

        # Find indirect variable position
        indirect_pos = next(
            (i for i, (name, _, _) in enumerate(all_vars) if name == indirect_var),
            None,
        )
        if indirect_pos is None:
            return None

        # Verify coefficients form valid stride pattern
        expected = 1
        for _, coeff, length in reversed(all_vars[indirect_pos + 1 :]):
            if coeff != expected:
                return None
            expected *= length
        if indirect_coeff != expected:
            return None

        return {
            "indirect_var": indirect_var,
            "indirect_dim": indirect_pos,
            "dims_before": [(n, l) for n, _, l in all_vars[:indirect_pos]],
            "dims_after": [(n, l) for n, _, l in all_vars[indirect_pos + 1 :]],
            "is_point_scatter": False,
            "output_shape": None,
        }