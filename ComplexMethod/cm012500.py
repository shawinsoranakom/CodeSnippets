def _decompose_strided_access(
        self, index: sympy.Expr, name: str
    ) -> list[tuple[int, int, int]] | None:
        """Decompose a flat index into per-dimension (stride, offset, skip) triples.

        Given flat index like ``64*x0 + 2*x1 + 5`` and buffer shape ``(32, 64)``
        with C-contiguous strides ``[64, 1]``:
          - x0 coefficient 64 / buffer_stride[0]=64 -> dim 0: stride=1
          - x1 coefficient 2 / buffer_stride[1]=1  -> dim 1: stride=2
          - constant 5: dim 0 gets 5//64=0, dim 1 gets 5//1=5
          - dim 1 offset 5 with stride 2: skip=5//2=2, offset=5%2=1

        Returns per-dim ``[(stride, offset, skip), ...]`` where:
          - stride: access stride on this dim (1 = contiguous)
          - offset: static index into the stride dim (0 <= offset < stride)
          - skip: number of stride-blocks to skip at the start of this dim
        Returns None if decomposition fails.
        """
        if self._has_indirect_vars(index) or index.has(ModularIndexing):
            return None

        # Don't reshape a buffer that already has flatten+gather loads;
        # the reshape would change the flat layout and break those loads.
        if name in self.flatten_indexed_buffers:
            return None

        info = self._get_buffer_info(name)
        if info is None:
            return None
        _, buf_size, _, _, _ = info

        buf_shape_or_none = [self._safe_int(s) for s in buf_size]
        if any(s is None or s <= 0 for s in buf_shape_or_none):
            return None
        buf_shape: list[int] = cast(list[int], buf_shape_or_none)
        ndim = len(buf_shape)
        if ndim == 0:
            return None

        c_strides = self._c_contiguous_strides(buf_shape)

        # Extract per-variable coefficients
        used_vars = self._get_used_iter_vars(index)
        if not used_vars:
            return None

        # [stride, raw_offset] per dim — raw_offset may be >= stride
        result: list[list[int]] = [[1, 0] for _ in range(ndim)]
        # Track which variable maps to which dimension
        var_to_dim: dict[sympy.Symbol, int] = {}

        remaining = V.graph.sizevars.simplify(index)
        for var in used_vars:
            var_expr = BlockPatternMatcher.get_subexpr_involving_symbol(remaining, var)
            coeff = BlockPatternMatcher.match_affine_block_expr(var_expr, var)
            if coeff is None:
                return None
            coeff_int = self._safe_int(coeff)
            if coeff_int is None or coeff_int <= 0:
                return None

            # Find which buffer dim this variable maps to
            dim = None
            for d in range(ndim):
                if c_strides[d] == 0:
                    continue
                if coeff_int % c_strides[d] == 0:
                    per_dim_stride = coeff_int // c_strides[d]
                    if per_dim_stride >= 1:
                        dim = d
                        break
            if dim is None:
                return None

            per_dim_stride = coeff_int // c_strides[dim]
            if per_dim_stride < 1 or buf_shape[dim] % per_dim_stride != 0:
                return None

            result[dim][0] = per_dim_stride
            var_to_dim[var] = dim
            remaining = V.graph.sizevars.simplify(remaining - var_expr)

        # Remaining is the constant offset; distribute across dims using
        # divmod with C-contiguous strides (largest stride first).
        offset_val = self._safe_int(remaining)
        if offset_val is None:
            return None
        if offset_val < 0:
            return None
        for d in range(ndim):
            if c_strides[d] > 0:
                result[d][1] = offset_val // c_strides[d]
                offset_val = offset_val % c_strides[d]
        if offset_val != 0:
            return None

        # Only return if there's at least one dim with stride > 1.
        # Contiguous accesses with just an offset (stride=1 everywhere)
        # are handled by the normal tiling path.
        if all(s == 1 for s, _ in result):
            return None

        # Decompose each dim's raw offset into (skip, offset) where
        # offset < stride: raw = skip * stride + offset.
        # Then validate the output numel matches.
        decomposed: list[tuple[int, int, int]] = []
        output_numel_expected = 1
        for d in range(ndim):
            stride, raw_offset = result[d]
            offset = raw_offset % stride
            skip = raw_offset // stride
            n_blocks = buf_shape[d] // stride
            if skip >= n_blocks:
                return None
            output_numel_expected *= n_blocks - skip
            decomposed.append((stride, offset, skip))

        output_numel, _ = self._compute_output_numel_from_index(index)
        if output_numel != output_numel_expected:
            return None

        # Verify each variable's range matches its assigned dimension's
        # effective size.  When the kernel collapses multiple buffer dims
        # into one iteration variable (e.g. batch*channels), the variable
        # range won't match any single buffer dimension and we must bail
        # out to avoid shape mismatches in the generated code.
        for var, dim in var_to_dim.items():
            if var not in self.range_tree_nodes:
                return None
            var_range = self._safe_int(self.range_tree_nodes[var].length)
            if var_range is None:
                return None
            stride_d, _offset_d, skip_d = decomposed[dim]
            effective_size = buf_shape[dim] // stride_d - skip_d
            if var_range != effective_size:
                return None

        return decomposed