def _scatter_dim_after_reshape(
    reshape_node: torch.fx.Node, orig_scatter_dim: int
) -> int:
    """
    Given a reshape node and the original scatter dim for the target tensor,
    returns the new scatter dim for the reshaped tensor.
    """
    # if there was no pre-mm reshape, scatter dim will not change.
    if not reshape_node:
        return orig_scatter_dim

    reshape_op_output_tensor = _get_tensor(reshape_node)
    assert reshape_op_output_tensor.ndim == 2, (
        "reshape must produce 2D tensor for scaled_mm"
    )

    assert len(reshape_node.args) >= 1, "reshape node must have at least 1 arg"
    input_tensor_node = cast(torch.fx.Node, reshape_node.args[0])
    reshape_op_input_tensor = _get_tensor(input_tensor_node)
    assert reshape_op_input_tensor.ndim > reshape_op_output_tensor.ndim, (
        "reshape must be from 3D+ to 2D"
    )

    # Note: for a N-D tensor to be reshaped into 2D, either the leading dims or ending dims must
    # be collapsed to a single dim. First determine which of these happened.
    input_shape = reshape_op_input_tensor.shape
    output_shape = reshape_op_output_tensor.shape
    leading_dims_collapsed = output_shape[0] == prod(input_shape[:-1])

    # Case 1: scatter dim 0 always maps to 0 after any reshape from 3D+ to 2D, regardless if
    # leading dims or ending dims were collapsed.
    if orig_scatter_dim == 0:
        return 0

    # Case 2: scatter dim "ndim-1" always maps to 1 after any reshape from 3D+ to 2D, regardless if
    # leading dims or ending dims were collapsed.
    if orig_scatter_dim == reshape_op_input_tensor.ndim - 1:
        return 1

    # Case 3: scatter dim was one of the middle dims (between 0 and ndim-1).
    # if the leading dims were collapsed, the new scatter dim will be 0.
    # if the ending dims were collapsed, the new scatter dim will be 1.
    return 0 if leading_dims_collapsed else 1