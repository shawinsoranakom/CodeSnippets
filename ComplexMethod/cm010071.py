def meta_fft_c2c(self, dim, normalization, forward):
    torch._check(self.dtype.is_complex)
    if not dim:
        return self.clone()

    if device_hint(self) == "cpu" and not torch.backends.mkl.is_available():
        return self.new_empty(self.size())

    out_sizes = self.size()
    output = self.new_empty(out_sizes)
    if device_hint(self) != "cuda":
        sorted_dims = _sort_dims(self, dim)
        return _exec_fft(output, self, out_sizes, sorted_dims, forward=forward)

    # Match _fft_c2c_cufft, which re-sorts the remaining dimensions after each
    # staged transform because _exec_fft restrides the output in place.
    sorted_dims = list(dim)
    working_tensor = self
    while True:
        strides = working_tensor.stride()
        sorted_dims.sort(key=lambda i: strides[i], reverse=True)
        max_dims = min(cufft_max_ndim, len(sorted_dims))
        last_dims = sorted_dims[len(sorted_dims) - max_dims :]

        _exec_fft(output, working_tensor, out_sizes, last_dims, forward=forward)
        sorted_dims = sorted_dims[: len(sorted_dims) - max_dims]

        if not sorted_dims:
            return output

        if working_tensor is self:
            working_tensor = output
            output = self.new_empty(out_sizes)
        else:
            output, working_tensor = working_tensor, output