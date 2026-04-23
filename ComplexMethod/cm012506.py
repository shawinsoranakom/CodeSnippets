def _can_use_tma_approach(self) -> bool:
        """
        Check if TMA (Tensor Memory Accelerator) approach can be used.
        TMA works for simple element-wise ops but not for:
        - Reductions (need different accumulation patterns)
          TODO: TMA supports float64 for loading but not for reductions
        - Broadcasting (inputs have different shapes or output differs)
        - Non-contiguous tensors (strided, transposed)
        """
        # TMA flattens to 1D tiles, incompatible with permutation detection
        # which emits jnp.permute_dims expecting N-D input.
        if self.permuted_input_buffers:
            return False

        # Check for reductions
        reduction_numel = self._compute_reduction_numel()
        if reduction_numel is not None and reduction_numel > 1:
            return False

        # Check all input buffers for contiguity, dtype, and shape consistency
        input_shapes: list[tuple] = []
        for name in self.args.input_buffers:
            info = self._get_buffer_info(name)
            if info is None:
                return False
            buf_obj, buf_size, buf_numel, actual_strides, is_contiguous = info
            if not is_contiguous:
                return False

            # Check for unsupported dtypes
            # TODO: TMA supports float64 for loading but current JAX Mosaic GPU
            # implementation doesn't support it yet. Re-enable when JAX adds support.
            buf_dtype = getattr(buf_obj, "get_dtype", lambda: None)()
            if buf_dtype is not None:
                import torch

                if buf_dtype == torch.float64:
                    return False

            # Collect shape as tuple for comparison
            shape_tuple = tuple(self._safe_int(s) for s in buf_size)
            if None in shape_tuple:
                return False  # Dynamic shapes not supported
            input_shapes.append(shape_tuple)

        # Check if all input shapes are identical (no broadcasting)
        if input_shapes and len(OrderedSet(input_shapes)) > 1:
            return False

        # Check that output numel matches input numel (no broadcasting expansion)
        if input_shapes:
            input_numel = 1
            for s in input_shapes[0]:
                input_numel *= s

            # Compute output numel from pointwise range trees (non-reduction)
            output_numel = 1
            for tree in self.range_trees:
                if not tree.is_reduction:
                    numel = self._safe_int(tree.numel)
                    if numel is None:
                        return False  # Dynamic shapes not supported
                    output_numel *= numel

            if output_numel != input_numel:
                return False

        return True