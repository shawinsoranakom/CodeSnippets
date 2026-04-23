def _stack_and_check_tensors(
    list_of_list_of_tensors, inputs, numel_outputs
) -> tuple[tuple[torch.Tensor, ...], bool, bool]:
    # For the ith tensor in the inner list checks whether it has the same size and
    # dtype as the ith differentiable input.
    out_jacobians = _allocate_jacobians_with_inputs(inputs, numel_outputs)
    diff_input_list = list(_iter_tensors(inputs, True))
    correct_grad_sizes = True
    correct_grad_types = True
    for i, tensor_list in enumerate(list_of_list_of_tensors):
        inp = diff_input_list[i]
        out_jacobian = out_jacobians[i]
        for j, tensor in enumerate(tensor_list):
            if tensor is not None and tensor.size() != inp.size():
                correct_grad_sizes = False
            elif tensor is not None and tensor.dtype != inp.dtype:
                correct_grad_types = False
            if tensor is None:
                out_jacobian[:, j].zero_()
            else:
                dense = tensor.to_dense() if tensor.layout != torch.strided else tensor
                if out_jacobian[:, j].numel() != dense.numel():
                    raise AssertionError(
                        f"Expected out_jacobian column to have {dense.numel()} elements, "
                        f"but got {out_jacobian[:, j].numel()}"
                    )
                out_jacobian[:, j] = dense.reshape(-1)
    return out_jacobians, correct_grad_sizes, correct_grad_types