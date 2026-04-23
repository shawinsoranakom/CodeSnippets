def _get_index_expr(self, index: sympy.Expr) -> _BufferIndexing:
        """Get the index expression string and whether it needs flattening."""
        has_indirect = self._has_indirect_vars(index)
        has_iter_vars = self._has_iteration_vars(index)

        if has_indirect and has_iter_vars:
            return _BufferIndexing(
                index_str=self._handle_mixed_indexing(index), needs_flatten=True
            )
        elif has_indirect:
            return _BufferIndexing(index_str=self.kexpr(index), needs_flatten=False)
        else:
            index_str = self._get_index_str(index)
            # Check if index contains ModularIndexing - this requires flattened access
            # ModularIndexing is used for roll/wrap-around operations
            needs_flatten = index.has(ModularIndexing) and index_str != "..."
            # If index_str is an actual expression (not "..." or a slice pattern),
            # we need flattened access because it uses block variables
            if not needs_flatten and index_str != "...":
                # Check if it's a simple slice pattern (::N or M::N)
                if not ("::" in index_str or index_str.lstrip("-").isdigit()):
                    needs_flatten = True
            return _BufferIndexing(index_str=index_str, needs_flatten=needs_flatten)