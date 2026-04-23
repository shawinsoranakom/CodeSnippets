def cat(g: jit_utils.GraphContext, tensor_list, dim):
    """Implement concatenation of pytorch tensors in ONNX along the specified `dim` dimension.

    Parameters:
        g (jit_utils.GraphContext): Graph context.
        tensor_list (List[torch.Tensor]): List of tensors to concatenate.
        dim (int): Dimension along which to concatenate the tensors.

    Returns:
        ONNX graph node representing the concatenated tensor.
    """
    tensors = symbolic_helper._unpack_list(tensor_list)
    # torch.cat ignores empty tensors such as `torch.Tensor([])`
    # These needs to be removed as input from ONNX's concat too, otherwise shape inference
    # will likely fail due to inputs with different ranks (0 for empty tensor, > 0 for anything else)
    nonempty_tensors = []
    for t in tensors:
        if symbolic_helper._is_constant(t) and not symbolic_helper._get_tensor_dim_size(
            t, 0
        ):
            continue
        nonempty_tensors.append(t)
    if len(nonempty_tensors) == 0:
        raise AssertionError("nonempty_tensors must not be empty")
    if not all(
        symbolic_helper._get_tensor_rank(nonempty_tensors[0]) is None
        or symbolic_helper._get_tensor_rank(t) is None
        or symbolic_helper._get_tensor_rank(t)
        == symbolic_helper._get_tensor_rank(nonempty_tensors[0])
        for t in nonempty_tensors
    ):
        raise AssertionError("All tensors must have the same rank")
    tensor_list.node().removeAllInputs()
    for t in nonempty_tensors:
        tensor_list.node().addInput(t)

    tensors = symbolic_helper._unpack_list(tensor_list)
    return g.op("Concat", *tensors, axis_i=dim)