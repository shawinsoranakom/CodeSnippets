def _detect_indirect_access(
        self, buf: str, name: str, index: sympy.Expr
    ) -> _IndirectAccessInfo | None:
        """Detect a load with data-dependent indexing suitable for scalar prefetch.

        Matches exactly one indirect variable whose coefficient corresponds to
        a C-contiguous stride dimension.  Rejects 1-to-1 gather patterns where
        the indices buffer covers the full iteration space.
        """
        buf_info = self._get_buffer_info(name)
        if buf_info is None:
            return None
        _, buf_size, _, _, _ = buf_info
        buf_size_raw = [self._safe_int(s) for s in buf_size]
        if len(buf_size_raw) < 2 or any(s is None for s in buf_size_raw):
            return None
        buf_size_ints: list[int] = cast(list[int], buf_size_raw)

        indirect_vars = self._get_indirect_vars(index)
        if len(indirect_vars) != 1:
            return None
        indirect_var = indirect_vars[0]

        coeff = self._get_index_coefficient(index, indirect_var)
        if coeff == 0 or not isinstance(coeff, int):
            return None

        # Use existing stride mapping to find which dimension is indirected
        strides = self._c_contiguous_strides(buf_size_ints)
        mapping = self._map_coeffs_to_dims([coeff], strides)
        if mapping is None:
            return None
        indirect_dim = mapping[0]

        ndim = len(buf_size_ints)
        if indirect_dim >= max(1, ndim - 2):
            return None

        indirect_var_name = str(indirect_var)
        indices_param = self._trace_to_load_source(indirect_var_name)
        if indices_param is None:
            return None

        # Reject gather patterns: only 1-D static index tensors supported
        indices_graph_name = self._param_to_graph_name.get(indices_param)
        if indices_graph_name is not None:
            indices_info = self._get_buffer_info(indices_graph_name)
            if indices_info is not None:
                _, indices_size, _, _, _ = indices_info
                if len(indices_size) != 1:
                    return None
                if self._safe_int(indices_size[0]) is None:
                    return None
                indices_numel = math.prod(
                    v for s in indices_size if (v := self._safe_int(s)) is not None
                )
                iter_product = math.prod(
                    length
                    for var in self._get_used_iter_vars(index)
                    if var in self.range_tree_nodes
                    if (length := self._safe_int(self.range_tree_nodes[var].length))
                    is not None
                )
                if indices_numel >= iter_product:
                    return None

        return _IndirectAccessInfo(
            table_param=buf,
            table_buf_name=name,
            table_shape=tuple(buf_size_ints),
            indirect_dim=indirect_dim,
            indirect_var=indirect_var_name,
            indices_param=indices_param,
        )