def index_add(g: jit_utils.GraphContext, self, dim, index, other, alpha=None):
    warnings.warn(
        "Warning: ONNX export does not support duplicated values in 'index' field, "
        + "this will cause the ONNX model to be incorrect.",
        stacklevel=2,
    )

    # ONNX does not support "alpha" argument, unlike aten index_add
    # See: https://github.com/pytorch/pytorch/pull/65993#issuecomment-953151102 for more context
    if alpha and symbolic_helper._scalar(symbolic_helper._maybe_get_scalar(alpha)) != 1:
        return symbolic_helper._unimplemented("index_add", "alpha != 1", self)

    dim = symbolic_helper._maybe_get_const(dim, "i")
    if dim is None:
        raise errors.SymbolicValueError(
            "ONNX export does NOT support exporting 'index_add_()' function with "
            "unknown 'dim' value.",
            self,
        )

    self_dim_rank = symbolic_helper._get_tensor_rank(self)
    other_dim_rank = symbolic_helper._get_tensor_rank(other)

    if self_dim_rank is None or other_dim_rank is None:
        raise errors.SymbolicValueError(
            "ONNX export does NOT support exporting 'index_add_()' function while "
            "the rank of self tensor or tensor to be added is unknown.",
            self,
        )

    if other_dim_rank != self_dim_rank:
        delta = self_dim_rank - other_dim_rank
        for _ in range(delta):
            other = symbolic_helper._unsqueeze_helper(
                g, other, [symbolic_helper._get_tensor_rank(other)]
            )

    other_dim_size = symbolic_helper._get_tensor_dim_size(other, dim)
    self_dim_size = symbolic_helper._get_tensor_dim_size(self, dim)

    if (other_dim_size is not None) and (self_dim_size is not None):
        if other_dim_size > self_dim_size:
            raise errors.SymbolicValueError(
                "ONNX export does not support exporting 'index_add_()' function with "
                "duplicated values in 'index' parameter yet.",
                self,
            )

    # Construct a new shape. It's almost as same as self except the size of the 'dim'
    # dimension is 1, so that we can expand other dimensions as expected.
    new_shape_axes = list(range(self_dim_rank))
    new_shape_starts = [0 for i in range(self_dim_rank)]
    new_shape_ends = [sys.maxsize if (i != dim) else 1 for i in range(self_dim_rank)]

    new_shape = symbolic_helper._slice_helper(
        g, self, axes=new_shape_axes, starts=new_shape_starts, ends=new_shape_ends
    )
    other = expand_as(g, other, new_shape)

    for _ in range(dim):
        index = symbolic_helper._unsqueeze_helper(g, index, [0])

    for _ in range(self_dim_rank - dim - 1):
        index = symbolic_helper._unsqueeze_helper(
            g, index, [symbolic_helper._get_tensor_rank(index)]
        )

    return scatter_add(g, self, dim, expand_as(g, index, other), other)