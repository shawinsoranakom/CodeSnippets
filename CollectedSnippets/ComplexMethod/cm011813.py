def index_put_impl_(self, indices, values, accumulate, check, may_realize=False):
    if may_realize:

        def indice_slice_from_randperm(indice):
            # Refer to: https://github.com/pytorch/pytorch/pull/139366#discussion_r1825424660
            # For this specific pattern, indices is unique as coming from torch.randperm.
            # However, as the content of the indices is unknown, we have to check this specific pattern.
            if isinstance(indice, TensorBox) and isinstance(indice.data, ir.BaseView):
                indice = indice.data.unwrap_view()
                return (
                    isinstance(indice, ir.StorageBox)
                    and isinstance(indice.data, ir.ExternKernel)
                    and getattr(indice.data, "fx_node", None)
                    and indice.data.fx_node.target is torch.ops.aten.randperm.default
                )
            return False

        if ir.try_get_name(self) in values.get_read_names() and not all(
            indice_slice_from_randperm(indice) for indice in indices
        ):
            # Fix issue: https://github.com/pytorch/pytorch/issues/138908
            # When self and values have memory overlapping, indices may
            # contain duplicate values, potentially causing incorrect results since
            # the load of `values` might contain modified value from the store of `self`.
            # To address this, store values in a temporary buffer in such cases.
            values.realize()

    # Dispatch to masked fill for single boolean index with single value
    if (
        values.get_numel() == 1
        and len(indices) == 1
        and indices[0].get_dtype() in (torch.bool, torch.uint8)
    ):
        mask = indices[0]
        for _ in range(len(mask.get_size()), len(self.get_size())):
            mask = unsqueeze(mask, -1)
        return index_put_as_masked_fill(self, [mask], values, accumulate)

    # Fallback in torch deterministic mode
    if torch.are_deterministic_algorithms_enabled():
        return index_put_fallback(self, indices, values, accumulate)

    # Fallback if there is a boolean index
    for index in indices:
        if index is not None and index.get_dtype() in (torch.bool, torch.uint8):
            return index_put_fallback(self, indices, values, accumulate)

    x_size = self.get_size()
    x_ndim = len(x_size)

    if accumulate and needs_fallback_due_to_atomic_add_limitations(self.get_dtype()):
        # self is an scalar Tensor
        if x_ndim == 0:
            self = view(self, [1])
        self = index_put_fallback(self, indices, values, accumulate)
        if x_ndim == 0:
            self = view(self, [])
        return self

    values = to_dtype(values, self.get_dtype())

    try:
        # Note that code will only get here when dtype is uint32
        indices, tensor_indices = check_and_broadcast_indices(
            indices, self.get_device()
        )
    except NotImplementedError:
        return index_put_fallback(self, indices, values, accumulate)

    indices_loaders = [i.make_loader() if i is not None else None for i in indices]

    assert isinstance(self, TensorBox)
    self.realize()

    # self is an scalar Tensor
    if x_ndim == 0:
        self = view(self, [1])

    # We can use the first one since they are all required to be the same size
    tensor_size = list(indices[tensor_indices[0]].get_size())
    indexed_size = [x_size[i] for i in range(len(indices))]

    expected_vals_size, inner_fn = index_output_size_and_inner_fn(
        x_size,
        indices,
        tensor_indices,
        tensor_size,
        indices_loaders,
        indexed_size,
        None,
        check=check,
    )
    values = expand(values, expected_vals_size)
    # all guards are set above during broadcast_tensors and expand

    device = self.get_device()
    assert device is not None
    scatter = ir.Scatter(
        device=device,
        dtype=self.get_dtype(),
        inner_fn=values.make_loader(),
        ranges=expected_vals_size,  # iter_ranges,
        output_indexer=inner_fn,
        scatter_mode="atomic_add" if accumulate else None,
    )
    buffer = ir.ComputedBuffer(
        name=None,
        layout=ir.MutationLayoutSHOULDREMOVE(self),
        data=scatter,
    )
    buffer.name = V.graph.register_buffer(buffer)
    V.graph.register_operation(buffer)

    if x_ndim == 0:
        self = view(self, [])
    return self