def _maybe_broadcast_1d_buffer(
        self, name: str, index: sympy.Expr, load_expr: str
    ) -> str:
        """Reshape 1D buffers for higher-dim broadcasting in reduction kernels.

        When a 1D buffer (e.g. a reduction result from a prior kernel, or a
        batch-norm parameter) is loaded into a kernel with 2+ iteration dims,
        JAX right-aligns it for broadcasting: (N,) becomes (1, N).  This is
        wrong when the buffer corresponds to a non-trailing axis; we reshape
        to (N, 1, ...) so broadcasting matches the correct axis.
        """
        buf_obj = V.graph.get_buffer(name)
        if buf_obj is None or len(buf_obj.get_size()) != 1:
            return load_expr

        # Only graph inputs, not intermediate buffers — intermediates are
        # already shaped by the IR and their dim order may not match the
        # reference buffer used below for axis inference.
        if name.startswith("buf"):
            return load_expr

        buf_length = self._safe_int(buf_obj.get_size()[0])
        if buf_length is None:
            return load_expr

        dtype = V.graph.get_dtype(name)
        if dtype is not None and not dtype.is_floating_point:
            return load_expr

        # Find a higher-dimensional reference buffer
        ref_buf_size = None
        for buf_name in self.args.input_buffers:
            other_buf = V.graph.get_buffer(buf_name)
            if other_buf is not None and len(other_buf.get_size()) > 1:
                ref_buf_size = [self._safe_int(s) for s in other_buf.get_size()]
                if all(s is not None for s in ref_buf_size):
                    break
                ref_buf_size = None
        if ref_buf_size is None or len(ref_buf_size) <= 1:
            return load_expr

        # Must use exactly one iteration variable
        used_vars = self._get_used_iter_vars(index)
        if len(used_vars) != 1:
            return load_expr
        used_var = next(iter(used_vars))
        if used_var not in self.range_tree_nodes:
            return load_expr

        # Verify buffer length matches variable length
        entry = self.range_tree_nodes[used_var]
        if self._safe_int(entry.length) != buf_length:
            return load_expr

        # Buffer length must uniquely match one non-reduction iteration variable.
        # If multiple pointwise vars share the same length (e.g. 2D pointwise
        # kernel with both dims equal), the axis is ambiguous and we bail out.
        matching_vars = [
            v
            for v, e in self.range_tree_nodes.items()
            if self._safe_int(e.length) == buf_length and not e.is_reduction
        ]
        if len(matching_vars) != 1:
            return load_expr

        # Determine axis position from the iteration variable's position
        # in the range tree (pointwise vars first, then reduction vars).
        axis_pos = None
        matching_dims = [i for i, s in enumerate(ref_buf_size) if s == buf_length]
        if len(matching_dims) == 1:
            axis_pos = matching_dims[0]
        else:
            # Ambiguous by size (e.g. square tensor with reduction).
            # Use the variable's position in the range tree.
            pw_idx = 0
            for sym, e in self.range_tree_nodes.items():
                if sym == used_var:
                    axis_pos = pw_idx
                    break
                if not e.is_reduction:
                    pw_idx += 1

        if axis_pos is None:
            return load_expr
        if axis_pos == len(ref_buf_size) - 1:
            return load_expr  # Last dim uses default broadcasting

        reshape_dims = [1] * len(ref_buf_size)
        reshape_dims[axis_pos] = -1
        return f"{load_expr}.reshape({', '.join(map(str, reshape_dims))})"