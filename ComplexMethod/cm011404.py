def tp_convolution_backward(
    op_call: torch._ops.OpOverload,
    local_tensor_args: tuple[object, ...],
    local_tensor_kwargs: dict[str, object],
    dim_map: list[int],
) -> object:
    if op_call != aten.convolution_backward.default:
        raise AssertionError
    if len(local_tensor_args) != 11:
        raise AssertionError

    rank = dist.get_rank()
    size = dist.get_world_size()
    grad_out_tensor = cast(torch.Tensor, local_tensor_args[0])
    in_tensor = cast(torch.Tensor, local_tensor_args[1])
    weight = cast(torch.Tensor, local_tensor_args[2])
    stride, padding, dilation = local_tensor_args[4:7]

    if not isinstance(padding, list):
        raise AssertionError

    if not _requires_data_exchange(padding, dim_map):
        local_results = op_call(*local_tensor_args, **local_tensor_kwargs)
        return local_results
    else:
        if not _is_supported(in_tensor.shape, weight.shape, stride, padding, dilation):
            raise AssertionError(
                "tp_convolution_backward data exchange requires supported stride/padding/dilation"
            )
        # step 0 compute the overlap pixels of the input tensor
        d = weight.shape[3] - 1
        d1 = d // 2
        d2 = d - d1
        if d1 + d2 != d:
            raise AssertionError
        right = (rank + 1) % size
        left = (rank - 1 + size) % size

        # step1 reconstruct local input tensor
        in_tensor = _ring_send_recv_construct(
            in_tensor, d1, d2, left, right, rank, size
        )

        # step2 reconstruct local gradient output tensor
        padding_w = padding[1]
        if rank == 0:
            grad_out_tensor = torch.nn.functional.pad(
                grad_out_tensor, (0, padding_w), "constant", 0
            )
        elif rank == size - 1:
            grad_out_tensor = torch.nn.functional.pad(
                grad_out_tensor, (padding_w, 0), "constant", 0
            )
        else:
            grad_out_tensor = torch.nn.functional.pad(
                grad_out_tensor, (padding_w, padding_w), "constant", 0
            )

        # step3 feed local input tensor to op_call
        local_tensor_args_list = list(local_tensor_args)
        local_tensor_args_list[0] = grad_out_tensor
        local_tensor_args_list[1] = in_tensor
        local_tensor_args = cast(tuple[object, ...], local_tensor_args_list)
        local_results = op_call(*local_tensor_args, **local_tensor_kwargs)

        # step4 aggregate gradients for edge pixels
        grad_in_tensor = local_results[0]
        if grad_in_tensor is not None:
            grad_in_tensor = _ring_send_recv_aggregate(
                grad_in_tensor, d1, d2, left, right, rank, size
            )
            local_results = list(local_results)
            local_results[0] = grad_in_tensor

        local_results = cast(tuple[object, ...], local_results)

        return local_results