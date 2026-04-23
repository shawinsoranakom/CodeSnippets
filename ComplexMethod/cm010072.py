def meta_fft_r2c(self, dim, normalization, onesided):
    torch._check(self.dtype.is_floating_point)
    input_sizes = list(self.size())
    out_sizes = list(input_sizes)
    last_dim = dim[-1]
    last_dim_halfsize = input_sizes[last_dim] // 2 + 1
    onesided_sizes = list(input_sizes)
    onesided_sizes[last_dim] = last_dim_halfsize

    if onesided:
        out_sizes[last_dim] = last_dim_halfsize

    if device_hint(self) == "cuda" or device_hint(self) == "xpu":
        # _fft_r2c_cufft in aten/src/ATen/native/cuda/SpectralOps.cpp
        # _fft_r2c_xpu in torch-xpu-ops/src/ATen/native/xpu/SpectralOps.cpp
        output = self.new_empty(
            out_sizes, dtype=utils.corresponding_complex_dtype(self.dtype)
        )

        working_tensor = self
        if device_hint(self) == "cuda" and use_optimized_cufft_path(dim):
            _exec_fft(output, working_tensor, out_sizes, dim, forward=True)
        else:
            # First do the R2C transform on the last dimension
            target_sizes = out_sizes if len(dim) == 1 else onesided_sizes
            _exec_fft(output, working_tensor, target_sizes, [last_dim], forward=True)
            if len(dim) > 1:
                working_tensor = self.new_empty(
                    out_sizes, dtype=utils.corresponding_complex_dtype(self.dtype)
                )

            # Then any remaining C2C transforms
            sorted_dims = dim[:-1]
            while sorted_dims:
                output, working_tensor = working_tensor, output
                strides = working_tensor.stride()
                sorted_dims.sort(
                    key=lambda i: strides[i], reverse=True
                )  # NB reverse!  Not sure if this is og bug
                max_dims = min(cufft_max_ndim, len(sorted_dims))
                last_dims = sorted_dims[len(sorted_dims) - max_dims :]
                _exec_fft(
                    output, working_tensor, onesided_sizes, last_dims, forward=True
                )
                sorted_dims = sorted_dims[: len(sorted_dims) - max_dims]

        if not onesided:
            if output.size(last_dim) != out_sizes[last_dim]:
                working_tensor.resize_(out_sizes, memory_format=torch.contiguous_format)
                output = working_tensor

        return output

    elif torch.backends.mkl.is_available():
        # _fft_r2c_mkl in aten/src/ATen/native/mkl/SpectralOps.cpp
        sorted_dims = _sort_dims(self, dim, exclude_last=True)
        output = self.new_empty(
            out_sizes, dtype=utils.corresponding_complex_dtype(self.dtype)
        )
        return _exec_fft(output, self, out_sizes, sorted_dims, forward=True)

    else:
        return self.new_empty(
            out_sizes, dtype=utils.corresponding_complex_dtype(self.dtype)
        )