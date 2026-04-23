def _sparse_coo_where(mask: Tensor, input: Tensor, fill_value: Tensor) -> Tensor:
    """Sparse variant of torch.where. Supports sparse COO and hybrid sparse COO tensors.

    _sparse_coo_where implements the following invariant:

      _sparse_coo_where(mask, input, fill_value).to_dense(fill_value) ==
        torch.where(mask.to_dense(), input.to_dense(), torch.full(input.shape, fill_value))

    where `a == b` means `assertEqual(a, b)`, mask is boolean sparse
    tensor, and `to_dense(fill_value)` is like `to_dense()` except
    that the unspecified elements are mapped to `fill_value` rather
    than to `0`.

    Returns a sparse COO tensor with the following features:

    - all specified elements correspond to masked-in elements that
      have the values of the input tensor. If there exists a masked-in
      element (as specified by mask) that is not specified in the
      input, in the result tensor, the corresponding element has value
      0. In the dense part of the sparse tensor, the masked-out
      elements are replaced with fill_value.

    - all unspecified elements correspond to masked-out elements.
    """

    if input.layout != torch.sparse_coo:
        raise AssertionError(f"input.layout must be sparse_coo, got {input.layout}")
    if mask.layout != input.layout:
        raise AssertionError(f"mask.layout must match input.layout, got {mask.layout}")
    if mask.shape != input.shape:
        raise AssertionError(
            f"mask.shape must match input.shape: {mask.shape} vs {input.shape}"
        )
    if mask.dense_dim() != input.dense_dim():
        # TODO: eliminate this restriction
        raise AssertionError(
            f"mask.dense_dim() must match input.dense_dim(): "
            f"{mask.dense_dim()} vs {input.dense_dim()}"
        )

    input = input.coalesce()

    # For set operations on sparse tensor indices, we'll convert
    # multi-dimensional indices to 1-D indices for efficiency.
    input_flat_indices = _sparse_coo_flatten_indices(
        input.indices(), input.shape[: input.sparse_dim()]
    )
    mask_flat_indices = _sparse_coo_flatten_indices(
        mask.indices(), mask.shape[: mask.sparse_dim()]
    )

    # the set of mask flat indices that define masked-in elements:
    if mask.dense_dim() > 0:
        mask_values = _any(
            mask.values(), tuple(range(1, input.sparse_dim() + 1)), False
        )
    else:
        mask_values = mask.values()
    maskin_flat_indices = mask_flat_indices[mask_values.nonzero()[:, 0]]

    def intersection(i1, i2):
        union, counts = torch.cat([i1, i2]).unique(return_counts=True)
        return union, torch.where(counts.gt(1))

    def minus(i1, i2):
        union, counts = torch.cat([i1, i2]).unique(return_counts=True)
        return intersection(union[torch.where(counts.eq(1))], i1)

    def _apply(a):
        obj, w = a
        return obj[w]

    # the set of input flat indices of specified and masked-in elements:
    maskin_input_flat_indices = _apply(
        intersection(maskin_flat_indices, input_flat_indices)
    )
    _, w = intersection(input_flat_indices, maskin_input_flat_indices)

    # the indices and values of masked-in elements
    where_input_indices = input.indices()[(slice(None),) + w]
    where_input_values = input.values()[w]

    if mask.dense_dim() > 0:
        # apply mask to the dense part of the input values:
        _, w1 = intersection(mask_flat_indices, maskin_input_flat_indices)
        where_mask_values = mask.values()[w1]
        where_input_values = torch.where(
            where_mask_values, where_input_values, fill_value
        )

    # the set of flat indices of unspecified input and masked-in elements:
    maskin_zero_flat_indices = _apply(
        minus(maskin_flat_indices, maskin_input_flat_indices)
    )

    # the indices of masked-in zero elements
    _, w = intersection(mask_flat_indices, maskin_zero_flat_indices)
    where_zero_indices = mask.indices()[(slice(None),) + w]

    # construct result
    n = where_zero_indices.size(1)
    if n == 0:
        # the input is coalesced, hence input_flat_indices are ordered
        # and the result is guaranteed to be coalesced:
        result = torch.sparse_coo_tensor(
            where_input_indices, where_input_values, input.shape
        )
        return result._coalesced_(True)

    where_indices = torch.cat([where_input_indices, where_zero_indices], dim=1)
    where_values = torch.cat(
        [
            where_input_values,
            where_input_values.new_zeros((n,) + where_input_values.shape[1:]),
        ]
    )
    result = torch.sparse_coo_tensor(where_indices, where_values, input.shape)

    # appending zero elements leads to uncoalesced sparse tensor
    return result.coalesce()