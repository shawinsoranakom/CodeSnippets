def _input_mask(input: Tensor | MaskedTensor, *args, **kwargs) -> Tensor:
    """Return canonical input mask.

    A canonical input mask is defined as a boolean mask tensor that
    shape and layout matches with the shape and the layout of the
    input.

    The canonical input mask is computed from the :attr:`mask` tensor
    content to meet the following criteria:

    1. The shape of the canonical input mask is the same as the shape
       of :attr:`input` tensor. If the mask tensor has a smaller shape
       than the shape of the :attr:`input`, broadcasting rules will be
       applied. Downcasting of mask is not supported.

    2. The layout of the canonical input mask is the same as the
       layout of the :attr:`input` tensor. If the mask has different
       layout, it will be converted to the expected layout.  In the
       case of sparse COO layout, the canonical input mask will be
       coalesced.

    3. The dtype of the canonical input mask is torch.bool. If the
       mask dtype is not bool then it will be converted to bool dtype
       using `.to(dtype=bool)` method call.

    4. The elements of the canonical input mask have boolean values
       copied from the content of the :attr:`mask` tensor (after
       possible broadcasting and dtype conversion transforms).  In
       general, the sparsity pattern of the sparse canonical input
       mask need not to be the same as the sparsity pattern of the
       sparse :attr:`input` tensor.

    """
    if input.layout not in {torch.strided, torch.sparse_coo, torch.sparse_csr}:
        raise ValueError(
            f"_input_mask expects strided or sparse COO or sparse CSR tensor but got {input.layout}"
        )

    mask = kwargs.get("mask")

    # default mask
    if mask is None:
        raise ValueError("_input_mask requires explicit mask")

    # mask shape must match with input shape
    if mask.shape != input.shape:
        if mask.ndim > input.ndim:
            raise IndexError(
                "_input_mask expected broadcastable mask (got mask dimensionality higher than of the input)"
            )
        if mask.layout == torch.strided:
            mask = torch.broadcast_to(mask.clone(), input.shape).to(dtype=torch.bool)
        elif mask.layout == torch.sparse_coo:
            mask = torch._sparse_broadcast_to(mask, input.shape)
        else:
            if mask.layout != torch.sparse_csr:
                raise AssertionError(f"expected sparse_csr layout, got {mask.layout}")
            # Broadcasting of CSR tensors is not implemented. Working
            # around by using COO layout.
            mask = torch._sparse_broadcast_to(
                mask.to_sparse(), input.shape
            ).to_sparse_csr()

    # mask layout must match with input layout
    if mask.layout != input.layout:
        if input.layout == torch.strided:
            mask = mask.to_dense()
        elif input.layout == torch.sparse_coo:
            if mask.layout == torch.strided:
                mask = mask.to_sparse(input.sparse_dim())
            else:
                mask = mask.to_sparse()
        else:
            if input.layout != torch.sparse_csr:
                raise AssertionError(f"expected sparse_csr layout, got {input.layout}")
            mask = mask.to_sparse_csr()

    # sparse mask must be coalesced
    if mask.layout == torch.sparse_coo:
        mask = mask.coalesce()

    # mask is a boolean tensor
    mask = mask.to(dtype=torch.bool)

    return mask