def meta_index_Tensor(self, indices):
    torch._check(bool(indices), lambda: "at least one index must be provided")
    # aten::index is the internal advanced indexing implementation
    # checkIndexTensorTypes and expandTensors
    result: list[Tensor | None] = []
    for i, index in enumerate(indices):
        if index is not None:
            torch._check(
                index.dtype in [torch.long, torch.int, torch.int8, torch.bool],
                lambda: "tensors used as indices must be long, int, byte or bool tensors",
            )
            if index.dtype in [torch.int8, torch.bool]:
                nonzero = index.nonzero()
                k = len(result)
                torch._check_index(
                    k + index.ndim <= self.ndim,
                    lambda: f"too many indices for tensor of dimension {self.ndim}",
                )
                for j in range(index.ndim):
                    torch._check_index(
                        index.shape[j] == self.shape[k + j],
                        lambda: f"The shape of the mask {index.shape} at index {i} "
                        f"does not match the shape of the indexed tensor {self.shape} at index {k + j}",
                    )
                    result.append(nonzero.select(1, j))
            else:
                result.append(index)
        else:
            result.append(index)
    indices = result
    torch._check(
        len(indices) <= self.ndim,
        lambda: f"too many indices for tensor of dimension {self.ndim} (got {len(indices)})",
    )
    # expand_outplace
    import torch._refs as refs  # avoid import cycle in mypy

    indices = list(refs._maybe_broadcast(*indices))
    # add missing null tensors
    while len(indices) < self.ndim:
        indices.append(None)

    # hasContiguousSubspace
    #   true if all non-null tensors are adjacent
    # See:
    # https://numpy.org/doc/stable/user/basics.indexing.html#combining-advanced-and-basic-indexing
    # https://stackoverflow.com/questions/53841497/why-does-numpy-mixed-basic-advanced-indexing-depend-on-slice-adjacency
    state = 0
    has_contiguous_subspace = False
    for index in indices:
        if state == 0:
            if index is not None:
                state = 1
        elif state == 1:
            if index is None:
                state = 2
        else:
            if index is not None:
                break
    else:
        has_contiguous_subspace = True

    # transposeToFront
    # This is the logic that causes the newly inserted dimensions to show up
    # at the beginning of the tensor, if they're not contiguous
    if not has_contiguous_subspace:
        dims = []
        transposed_indices = []
        for i, index in enumerate(indices):
            if index is not None:
                dims.append(i)
                transposed_indices.append(index)
        for i, index in enumerate(indices):
            if index is None:
                dims.append(i)
                transposed_indices.append(index)
        self = self.permute(dims)
        indices = transposed_indices

    # AdvancedIndex::AdvancedIndex
    # Now we can assume the indices have contiguous subspace
    # This is simplified from AdvancedIndex which goes to more effort
    # to put the input and indices in a form so that TensorIterator can
    # take them.  If we write a ref for this, probably that logic should
    # get implemented
    before_shape: list[int] = []
    after_shape: list[int] = []
    replacement_shape: list[int] = []
    for dim, index in enumerate(indices):
        if index is None:
            if replacement_shape:
                after_shape.append(self.shape[dim])
            else:
                before_shape.append(self.shape[dim])
        else:
            replacement_shape = list(index.shape)

    def _restride_src(self):
        """
        This follows restride_src in TensorAdvancedIndexing.cpp
        """
        shape = before_shape + replacement_shape + after_shape
        strides = list(self.stride())
        # pyrefly: ignore [unsupported-operation]
        strides[len(before_shape) : len(self.shape) - len(after_shape)] = [0] * len(
            replacement_shape
        )
        return self.as_strided(shape, strides)

    out = self.new_empty(before_shape + replacement_shape + after_shape)

    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if guard_or_false(self.numel() == 0):
        # No need to worry about the output strides if self is empty.
        return out

    # Try to follow eager to decide the output stride based on self.
    # Note that perm here is the reverse of the 'perm_' decided by
    # TensorIteratorBase::reorder_dimensions
    restrided_self = _restride_src(self)
    perm, _ = utils.compute_elementwise_output_logical_to_physical_perm(restrided_self)

    # Follow TensorIteratorBase::allocate_or_resize_outputs
    if list(perm) != list(range(len(perm))):
        perm_shape = utils.apply_perm(out.shape, perm)
        new_stride = utils.make_contiguous_strides_for(perm_shape)
        new_stride = utils.apply_perm(new_stride, utils.invert_perm(perm))
        out = out.as_strided(out.size(), new_stride)
    return out