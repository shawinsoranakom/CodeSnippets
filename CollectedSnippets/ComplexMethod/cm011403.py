def tp_convolution(
    op_call: torch._ops.OpOverload,
    local_tensor_args: tuple[object, ...],
    local_tensor_kwargs: dict[str, object],
    dim_map: list[int],
) -> object:
    if op_call != aten.convolution.default:
        raise AssertionError
    if len(local_tensor_args) != 9:
        raise AssertionError

    rank = dist.get_rank()
    size = dist.get_world_size()
    in_tensor = cast(torch.Tensor, local_tensor_args[0])
    weight = cast(torch.Tensor, local_tensor_args[1])
    stride, padding, dilation = local_tensor_args[3:6]

    if not isinstance(padding, list):
        raise AssertionError

    if not _requires_data_exchange(padding, dim_map):
        local_results = op_call(*local_tensor_args, **local_tensor_kwargs)
        return local_results
    else:
        if not _is_supported(in_tensor.shape, weight.shape, stride, padding, dilation):
            raise AssertionError(
                "tp_convolution data exchange requires supported stride/padding/dilation"
            )
        # step 0 compute the overlap pixels of the input tensor
        d = weight.shape[-1] - 1
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

        # step2 feed local input tensor to op_call
        local_tensor_args_list = list(local_tensor_args)
        local_tensor_args_list[0] = in_tensor
        local_tensor_args = cast(tuple[object, ...], local_tensor_args_list)
        local_results = op_call(*local_tensor_args, **local_tensor_kwargs)

        # step3 remove extra outputs from the results
        padding_w = padding[-1]
        w = local_results.size(-1)
        if rank == 0:
            local_results = local_results[..., : w - padding_w]
        elif rank == size - 1:
            local_results = local_results[..., padding_w:]
        else:
            local_results = local_results[..., padding_w : w - padding_w]

        return local_results