def _get_collapsed_load_permutation(
        self, name: str, index: sympy.Expr
    ) -> tuple[tuple[int, ...], tuple[int, ...]] | None:
        """Handle permutation when range tree has collapsed dimensions.

        When simplify_and_reorder merges contiguous dims, the range tree
        has fewer variables than the buffer's rank.  This method detects
        the permutation in the collapsed space and returns
        (collapsed_input_shape, perm) so the caller can generate:
            jnp.permute_dims(load.reshape(collapsed_shape), perm)

        Uses index coefficients on both sides: load-index coefficients
        map vars to collapsed input dims, and store-side coefficients
        (derived from the range tree nesting) map vars to collapsed
        output dims.  Both sets of strides are always unique, so
        matching is unambiguous even with duplicate group sizes.
        """
        info = self._get_buffer_info(name)
        if not info:
            return None
        _, buf_size, _, _, is_contiguous = info
        in_shape_raw = [self._safe_int(s) for s in buf_size]
        if len(in_shape_raw) < 2 or None in in_shape_raw:
            return None
        in_shape: list[int] = cast(list[int], in_shape_raw)
        if not is_contiguous:
            return None

        iter_used = self._get_used_iter_vars(index)
        ordered = [
            s
            for s, e in self.range_tree_nodes.items()
            if s in iter_used and not e.is_reduction
        ]
        n = len(ordered)
        if n < 2 or n >= len(in_shape):
            return None
        ranges_raw = [self._safe_int(self.range_tree_nodes[v].length) for v in ordered]
        if None in ranges_raw:
            return None
        ranges: list[int] = cast(list[int], ranges_raw)
        if math.prod(ranges) != math.prod(in_shape):
            return None

        # Group consecutive input dims (right-to-left) to match ranges
        in_groups = self._group_dims_to_ranges(in_shape, ranges)
        if in_groups is None:
            return None

        # Compute collapsed input strides (row-major) and use load-index
        # coefficients to map each range tree var to a collapsed input dim.
        # Strides are always unique, so this is unambiguous even when
        # group sizes are duplicated.
        collapsed_in_strides = [0] * n
        stride = 1
        for i in range(n - 1, -1, -1):
            collapsed_in_strides[i] = stride
            stride *= in_groups[i]

        simplified = V.graph.sizevars.simplify(index)
        in_coeffs_raw = [self._get_index_coefficient(simplified, v) for v in ordered]
        if not all(isinstance(c, int) and c > 0 for c in in_coeffs_raw):
            return None
        in_coeffs: list[int] = cast(list[int], in_coeffs_raw)

        in_stride_to_dim = {s: i for i, s in enumerate(collapsed_in_strides)}
        var_to_in_dim = []
        for coeff in in_coeffs:
            dim = in_stride_to_dim.get(coeff)
            if dim is None:
                return None
            var_to_in_dim.append(dim)

        store_coeffs = self._compute_store_coeffs(ordered)
        if store_coeffs is None:
            return None

        # Find the output-side mapping using store coefficients.
        for out_name in self._output_buffer_names:
            out_buf = V.graph.get_buffer(out_name)
            if out_buf is None:
                continue
            out_shape_raw = [self._safe_int(s) for s in out_buf.get_size()]
            if any(s is None for s in out_shape_raw) or len(out_shape_raw) < 2:
                continue
            out_shape: list[int] = cast(list[int], out_shape_raw)
            if math.prod(out_shape) != math.prod(in_shape):
                continue
            out_groups = self._group_dims_to_ranges(out_shape, list(in_groups))
            if out_groups is None:
                continue

            # Compute collapsed output strides and match store coefficients.
            collapsed_out_strides = [0] * n
            stride = 1
            for i in range(n - 1, -1, -1):
                collapsed_out_strides[i] = stride
                stride *= out_groups[i]

            out_stride_to_dim = {s: j for j, s in enumerate(collapsed_out_strides)}
            var_to_out_dim = []
            for v in ordered:
                j = out_stride_to_dim.get(store_coeffs[v])
                if j is None:
                    return None
                var_to_out_dim.append(j)

            # Build perm: perm[out_dim] = in_dim
            perm = [0] * n
            for k in range(n):
                perm[var_to_out_dim[k]] = var_to_in_dim[k]
            if perm == list(range(n)):
                return None
            return (tuple(in_groups), tuple(perm))
        return None