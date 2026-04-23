def clone_input(x: torch.Tensor, *, dtype: torch.dtype | None = None) -> torch.Tensor:
    """copy while preserving strides"""
    # TODO: this is questionable
    if is_fake(x):
        # this func fails on fake tensors in __torch_dispatch__
        return x

    def torch_clone(x: torch.Tensor) -> torch.Tensor:
        y = torch.clone(x)
        if x.is_leaf:
            y.requires_grad_(x.requires_grad)
        if x.is_leaf and x.grad is not None:
            y.grad = clone_input(x.grad, dtype=dtype)
        copy_dynamo_tensor_attributes(x, y)
        return y

    with torch.no_grad():
        if x.device.type == "xla":
            # Access data_ptr() for a xla tensor will cause crash
            return torch_clone(x)

        # Handle sparse storage (no stride).
        if x.layout is torch.sparse_coo:
            return torch.sparse_coo_tensor(
                torch_clone(x._indices()),
                torch_clone(x._values()),
                x.shape,
                is_coalesced=x.is_coalesced(),
            )
        elif is_sparse_compressed(x):
            if x.layout in {torch.sparse_csr, torch.sparse_bsr}:
                compressed_indices = x.crow_indices()
                plain_indices = x.col_indices()
            else:
                compressed_indices = x.ccol_indices()
                plain_indices = x.row_indices()
            return torch.sparse_compressed_tensor(
                torch_clone(compressed_indices),
                torch_clone(plain_indices),
                torch_clone(x.values()),
                x.shape,
                layout=x.layout,
            )
        elif is_traceable_wrapper_subclass(x):
            # Questionable - but this is required to not fail executorch related
            # torchao tests.
            return torch_clone(x)

        needed_size = sum(
            (shape - 1) * stride for shape, stride in zip(x.size(), x.stride())
        )
        if x.is_quantized:
            result = torch.empty_quantized((needed_size + 32,), x)
        else:
            result = torch.empty(
                needed_size + 32, dtype=dtype or x.dtype, device=x.device
            )
        cache_line_offset = (
            (x.data_ptr() - result.data_ptr()) % 32
        ) // x.element_size()
        result.as_strided_(x.size(), x.stride(), cache_line_offset)
        try:
            result.copy_(x.clone())
            if x.is_leaf:
                result.requires_grad_(x.requires_grad)
            if x.is_leaf and x.grad is not None:
                result.grad = clone_input(x.grad, dtype=dtype)
        except RuntimeError:
            # RuntimeError: unsupported operation: more than one element of the written-to
            # tensor refers to a single memory location. Please clone() the tensor before
            # performing the operation.
            return torch_clone(x)
        copy_dynamo_tensor_attributes(x, result)
        return result