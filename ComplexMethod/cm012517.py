def _check_im2col_pattern(
        self, index: sympy.Expr, indexing: _BufferIndexing
    ) -> _BufferIndexing:
        """
        Check for im2col-like patterns where store uses block variables but load doesn't.

        For cat/expand patterns, both load and store prepared indices share block vars.
        For im2col patterns, store compresses to block vars but load doesn't.
        """
        if indexing.index_str != "..." or indexing.needs_flatten:
            return indexing

        prepared_index = self.prepare_indexing(index)
        iter_vars = self._get_iter_vars()
        store_orig_vars = self._get_used_iter_vars(index)
        store_prep_vars = (
            prepared_index.free_symbols
            if hasattr(prepared_index, "free_symbols")
            else OrderedSet()
        ) & iter_vars
        new_vars = store_prep_vars - store_orig_vars

        # Only trigger if store introduces new block vars
        if not new_vars or len(store_orig_vars) <= 1:
            return indexing

        # Check if loads are compatible with broadcast or cat pattern
        has_im2col_pattern = False
        for buf_name, load_index in self.load_index_exprs.items():
            load_orig_vars = self._get_used_iter_vars(load_index)
            if not load_orig_vars:
                continue

            # Load has iteration variables
            if load_orig_vars != store_orig_vars:
                continue

            # Same vars - check if load gets compressed too
            prep_load = self.prepare_indexing(load_index)
            load_prep_vars = (
                prep_load.free_symbols
                if hasattr(prep_load, "free_symbols")
                else OrderedSet()
            ) & iter_vars

            # If store compresses but load doesn't, check for strided input vs im2col
            if load_orig_vars != load_prep_vars or store_prep_vars == store_orig_vars:
                continue

            # Check if load coefficients match buffer strides
            if not self._check_load_is_strided_input(
                buf_name, load_index, load_orig_vars
            ):
                has_im2col_pattern = True
                break

        if has_im2col_pattern:
            return _BufferIndexing(
                index_str=self._generate_strided_index(prepared_index),
                needs_flatten=True,
            )

        return indexing