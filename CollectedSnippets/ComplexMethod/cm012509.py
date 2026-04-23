def _needs_strided_indexing(
        self,
        name: str,
        index: sympy.Expr,
        indexing: _BufferIndexing,
    ) -> _BufferIndexing:
        """Check if buffer access needs strided indexing due to size mismatch or gather patterns."""
        # Only applies when full array access is indicated
        if indexing.index_str != "..." or indexing.needs_flatten:
            return indexing

        info = self._get_buffer_info(name)
        if info is None:
            return indexing

        buf_obj, buf_size, buf_numel, actual_strides, is_contiguous = info
        output_numel, used_vars = self._compute_output_numel_from_index(index)
        all_iter_vars = self._get_iter_vars()
        coefficients = self._get_index_coefficients(index, used_vars)

        # Check for gather pattern
        has_non_unit_strides = self._check_gather_pattern(
            buf_size, actual_strides, is_contiguous, coefficients
        )

        # Check for im2col-like pattern (more iter vars used than buffer dims)
        buf_effective_dims = sum(1 for s in buf_size if self._safe_int(s) != 1)
        not_all_vars_used = (
            len(used_vars) < len(all_iter_vars)
            and len(used_vars) > 0
            and buf_effective_dims > 1
            and len(used_vars) > len(buf_size)
        )

        # Check various conditions for skipping strided indexing
        is_tpu = V.graph.get_current_device_or_throw().type == "tpu"
        is_known_non_contiguous = not is_contiguous and all(
            s is not None for s in actual_strides
        )
        has_symbolic_coef = any(not isinstance(c, int | float) for c in coefficients)
        skip_for_non_contiguous = (
            is_known_non_contiguous and not is_tpu and buf_numel == output_numel
        )

        # Determine if strided indexing is needed
        if (
            output_numel > 0
            and (buf_numel != output_numel or not_all_vars_used or has_non_unit_strides)
            and len(used_vars) > 0
            and not skip_for_non_contiguous
            and not has_symbolic_coef
        ):
            return _BufferIndexing(
                index_str=self._generate_strided_index(index), needs_flatten=True
            )

        return indexing