def _exec_fft(out, self, out_sizes, dim, *, forward):
    ndim = self.ndim
    signal_ndim = len(dim)
    batch_dims = ndim - signal_ndim

    # Permute dimensions so batch dimensions come first, and in stride order
    dim_permute = list(range(ndim))

    is_transformed_dim = [False for _ in range(ndim)]
    for d in dim:
        is_transformed_dim[d] = True

    # std::partition + std::copy(dim.begin(), dim.end(), batch_end)
    left = [d for d in dim_permute if not is_transformed_dim[d]]
    dim_permute = left + list(dim)
    batch_end = len(left)

    self_strides = self.stride()
    tmp = dim_permute[:batch_end]
    tmp.sort(key=lambda x: self_strides[x], reverse=True)
    dim_permute = tmp + dim_permute[batch_end:]
    input = self.permute(dim_permute)

    # Collapse batch dimensions into a single dimension
    batched_sizes = [-1] + list(input.shape[batch_dims:])
    input = input.reshape(batched_sizes)

    batch_size = input.size(0)
    batched_sizes[0] = batch_size
    batched_out_sizes = list(batched_sizes)
    for i in range(len(dim)):
        batched_out_sizes[i + 1] = out_sizes[dim[i]]
    out.resize_(batched_out_sizes, memory_format=torch.contiguous_format)

    # Inplace reshaping to original batch shape and inverting the dimension permutation
    out_strides = [0 for _ in range(ndim)]
    batch_numel = 1
    i = batch_dims - 1
    while i >= 0:
        out_strides[dim_permute[i]] = batch_numel * out.stride(0)
        batch_numel *= out_sizes[dim_permute[i]]
        i -= 1
    for i in range(batch_dims, ndim):
        out_strides[dim_permute[i]] = out.stride(1 + (i - batch_dims))
    out.as_strided_(out_sizes, out_strides, out.storage_offset())

    return out