def _adjust_index_for_buffer_shape(
        self,
        name: str,
        index: sympy.Expr,
        indexing: _BufferIndexing,
    ) -> _BufferIndexing:
        """
        Adjust index expression based on buffer shape (0-dim scalar, multi-dim, etc.).
        """
        if indexing.needs_flatten or indexing.index_str == "...":
            return indexing

        buf_obj = V.graph.get_buffer(name)
        if buf_obj is None:
            return indexing

        buf_size = buf_obj.get_size()

        # 0-dimensional (scalar) buffer - use [...] to access it
        if len(buf_size) == 0:
            return _BufferIndexing(
                index_str="...", needs_flatten=indexing.needs_flatten
            )

        # Multi-dimensional buffer with constant/scalar index
        if len(buf_size) > 1:
            has_iter_vars = self._has_iteration_vars(index)
            if not has_iter_vars:
                return _BufferIndexing(
                    index_str=indexing.index_str, needs_flatten=True
                )  # Use flattened access
            elif "::" in indexing.index_str:
                # Strided slice patterns need flattened indexing for multi-dim
                return _BufferIndexing(
                    index_str=self._generate_strided_index(index), needs_flatten=True
                )

        # GPU doesn't support gather from slice patterns on 1D buffers
        if self.is_gpu and "::" in indexing.index_str:
            return _BufferIndexing(
                index_str=self._generate_strided_index(index), needs_flatten=True
            )

        return indexing