def _check_load_is_strided_input(
        self, buf_name: str, load_index: sympy.Expr, load_orig_vars: OrderedSet
    ) -> bool:
        """
        Check if load coefficients match buffer strides (strided input vs im2col).
        """
        buf = V.graph.get_buffer(buf_name)
        if buf is None:
            return False

        layout = getattr(buf, "get_layout", lambda: None)()
        if layout is None:
            return False

        buf_strides = getattr(layout, "stride", None)
        if buf_strides is None:
            return False

        buf_sizes = buf.get_size()

        # Get load coefficients
        load_coeffs = []
        for var in load_orig_vars:
            var_expr = BlockPatternMatcher.get_subexpr_involving_symbol(load_index, var)
            coef = BlockPatternMatcher.match_affine_block_expr(var_expr, var)
            if coef is not None:
                int_coef = self._safe_int(coef)
                load_coeffs.append(int_coef if int_coef is not None else coef)

        # Check if coefficients match buffer strides
        # Only include strides for non-trivial dimensions (size > 1)
        buf_stride_set = OrderedSet()
        for i, s in enumerate(buf_strides):
            dim_size = self._safe_int(buf_sizes[i])
            if dim_size is None or dim_size > 1:
                int_s = self._safe_int(s)
                buf_stride_set.add(int_s if int_s is not None else s)

        return OrderedSet(load_coeffs) == buf_stride_set