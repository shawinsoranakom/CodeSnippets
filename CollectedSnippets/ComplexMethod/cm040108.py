def _get_kernel_scale_shape(self, kernel_shape, block_size=None):
        """Get the shape of the kernel scale tensor.

        The kernel scale tensor is used to scale the kernel tensor.
        The shape of the kernel scale tensor is the same as the shape of the
        kernel tensor, but with the reduced axes set to 1 (for per-channel)
        or n_groups (for grouped quantization), and the transpose axes set
        to the original axes.

        Args:
            kernel_shape: The shape of the kernel tensor.
            block_size: If provided and positive, use grouped quantization
                along the reduced axes with the specified block size.

        Returns:
            The shape of the kernel scale tensor.
        """
        if block_size is not None and block_size > 0:
            # Grouped quantization: use simple 2D scale shape
            # (n_groups, non_reduced) - matches dequantize_grouped format
            total_reduced_dim = 1
            for ax in self._kernel_reduced_axes:
                total_reduced_dim *= kernel_shape[ax]
            n_groups = math.ceil(total_reduced_dim / block_size)

            total_non_reduced = 1
            for i, dim in enumerate(kernel_shape):
                if i not in self._kernel_reduced_axes:
                    total_non_reduced *= dim

            return (n_groups, total_non_reduced)
        else:
            # Per-channel quantization: use the original transformation logic
            kernel_scale_shape = np.array(kernel_shape)
            kernel_scale_shape[self._kernel_reduced_axes] = 1

            kernel_scale_shape = kernel_scale_shape[self._kernel_transpose_axes]
            kernel_scale_shape = kernel_scale_shape.tolist()
            for a in sorted(self._kernel_expand_axes):
                kernel_scale_shape.insert(a, 1)
            for a in sorted(self._kernel_squeeze_axes, reverse=True):
                kernel_scale_shape.pop(a)
            return kernel_scale_shape