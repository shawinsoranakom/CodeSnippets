def _try_multidim_slice(
        self,
        name: str,
        index: sympy.Expr,
        indexing: _BufferIndexing,
    ) -> _BufferIndexing:
        """
        Try to emit multi-dim slice notation instead of flatten + gather.

        For a buffer with shape (d0, ..., dk) and index `stride * var + offset`,
        emit `buf[:, ..., :, offset::stride]` when stride divides dk.
        """
        if not indexing.needs_flatten:
            return indexing

        buf_obj = V.graph.get_buffer(name)
        if buf_obj is None:
            return indexing

        buf_size = buf_obj.get_size()
        ndim = len(buf_size)
        if ndim < 2:
            return indexing

        # Need a single iteration variable with an affine index
        used_vars = self._get_used_iter_vars(index)
        if len(used_vars) != 1:
            return indexing

        var = next(iter(used_vars))
        var_expr = BlockPatternMatcher.get_subexpr_involving_symbol(index, var)
        stride = self._safe_int(
            BlockPatternMatcher.match_affine_block_expr(var_expr, var)
        )
        if stride is None or stride <= 1:
            return indexing

        offset = V.graph.sizevars.simplify(index - var_expr)
        try:
            offset_val = int(offset)
        except (TypeError, ValueError):
            return indexing

        if offset_val < 0 or offset_val >= stride:
            return indexing

        last_dim = self._safe_int(buf_size[-1])
        if last_dim is None or last_dim % stride != 0:
            return indexing

        # Verify the iteration variable covers all buffer elements at the
        # given stride: var_length * stride == buf_numel. This ensures
        # the flattened stride-access 0, stride, 2*stride, ... maps exactly
        # to buf[:, ..., :, offset::stride].
        entry = self.range_tree_nodes.get(var)
        if entry is None:
            return indexing
        var_length = self._safe_int(entry.length)
        buf_numel = 1
        for s in buf_size:
            d = self._safe_int(s)
            if d is None:
                return indexing
            buf_numel *= d
        if var_length is None or var_length * stride != buf_numel:
            return indexing

        prefix = ":, " * (ndim - 1)
        if offset_val == 0:
            slice_str = f"{prefix}::{stride}"
        else:
            slice_str = f"{prefix}{offset_val}::{stride}"
        return _BufferIndexing(index_str=slice_str, needs_flatten=False)