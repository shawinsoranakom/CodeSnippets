def all_to_all_single(
    output,
    input,
    output_split_sizes=None,
    input_split_sizes=None,
    group=None,
    async_op: bool = False,
):
    """
    Split input tensor and then scatter the split list to all processes in a group.

    Later the received tensors are concatenated from all the processes in the group
    and returned as a single output tensor.

    Complex tensors are supported.

    Args:
        output (Tensor): Gathered concatenated output tensor.
        input (Tensor): Input tensor to scatter.
        output_split_sizes: (list[Int], optional): Output split sizes for dim 0
            if specified None or empty, dim 0 of ``output`` tensor must divide
            equally by ``world_size``.
        input_split_sizes: (list[Int], optional): Input split sizes for dim 0
            if specified None or empty, dim 0 of ``input`` tensor must divide
            equally by ``world_size``.
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (bool, optional): Whether this op should be an async op.

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group.

    .. warning::
        `all_to_all_single` is experimental and subject to change.

    Examples:
        >>> # xdoctest: +SKIP("Undefined rank")
        >>> input = torch.arange(4) + rank * 4
        >>> input
        tensor([0, 1, 2, 3])     # Rank 0
        tensor([4, 5, 6, 7])     # Rank 1
        tensor([8, 9, 10, 11])   # Rank 2
        tensor([12, 13, 14, 15]) # Rank 3
        >>> output = torch.empty([4], dtype=torch.int64)
        >>> dist.all_to_all_single(output, input)
        >>> output
        tensor([0, 4, 8, 12])    # Rank 0
        tensor([1, 5, 9, 13])    # Rank 1
        tensor([2, 6, 10, 14])   # Rank 2
        tensor([3, 7, 11, 15])   # Rank 3

        >>> # Essentially, it is similar to following operation:
        >>> scatter_list = list(input.chunk(world_size))
        >>> gather_list = list(output.chunk(world_size))
        >>> for i in range(world_size):
        >>>     dist.scatter(gather_list[i], scatter_list if i == rank else [], src = i)

        >>> # Another example with uneven split
        >>> input
        tensor([0, 1, 2, 3, 4, 5])                                       # Rank 0
        tensor([10, 11, 12, 13, 14, 15, 16, 17, 18])                     # Rank 1
        tensor([20, 21, 22, 23, 24])                                     # Rank 2
        tensor([30, 31, 32, 33, 34, 35, 36])                             # Rank 3
        >>> input_splits
        [2, 2, 1, 1]                                                     # Rank 0
        [3, 2, 2, 2]                                                     # Rank 1
        [2, 1, 1, 1]                                                     # Rank 2
        [2, 2, 2, 1]                                                     # Rank 3
        >>> output_splits
        [2, 3, 2, 2]                                                     # Rank 0
        [2, 2, 1, 2]                                                     # Rank 1
        [1, 2, 1, 2]                                                     # Rank 2
        [1, 2, 1, 1]                                                     # Rank 3
        >>> output = ...
        >>> dist.all_to_all_single(output, input, output_splits, input_splits)
        >>> output
        tensor([ 0,  1, 10, 11, 12, 20, 21, 30, 31])                     # Rank 0
        tensor([ 2,  3, 13, 14, 22, 32, 33])                             # Rank 1
        tensor([ 4, 15, 16, 23, 34, 35])                                 # Rank 2
        tensor([ 5, 17, 18, 24, 36])                                     # Rank 3


        >>> # Another example with tensors of torch.cfloat type.
        >>> input = torch.tensor(
        ...     [1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j], dtype=torch.cfloat
        ... ) + 4 * rank * (1 + 1j)
        >>> input
        tensor([1+1j, 2+2j, 3+3j, 4+4j])                                # Rank 0
        tensor([5+5j, 6+6j, 7+7j, 8+8j])                                # Rank 1
        tensor([9+9j, 10+10j, 11+11j, 12+12j])                          # Rank 2
        tensor([13+13j, 14+14j, 15+15j, 16+16j])                        # Rank 3
        >>> output = torch.empty([4], dtype=torch.int64)
        >>> dist.all_to_all_single(output, input)
        >>> output
        tensor([1+1j, 5+5j, 9+9j, 13+13j])                              # Rank 0
        tensor([2+2j, 6+6j, 10+10j, 14+14j])                            # Rank 1
        tensor([3+3j, 7+7j, 11+11j, 15+15j])                            # Rank 2
        tensor([4+4j, 8+8j, 12+12j, 16+16j])                            # Rank 3
    """
    # Dynamo has built-in logic to map legacy distributed ops to functional collectives.
    # Let's redirect to a torch function mode that can mimic this logic outside Dynamo
    # (e.g., non-strict export implements such a torch function mode).
    relevant_args = (input,)
    if has_torch_function(relevant_args):
        return handle_torch_function(
            all_to_all_single,
            relevant_args,
            output,
            input,
            output_split_sizes=output_split_sizes,
            input_split_sizes=input_split_sizes,
            group=group,
            async_op=async_op,
        )

    if _rank_not_in_group(group):
        _warn_not_in_group("all_to_all_single")
        return

    opts = AllToAllOptions()
    opts.asyncOp = async_op
    _check_single_tensor(output, "output")
    _check_single_tensor(input, "input")
    _ensure_all_tensors_same_dtype(output, input)

    if input.is_complex():
        input = torch.view_as_real(input)
    if output.is_complex():
        output = torch.view_as_real(output)

    output_split_sizes = [] if output_split_sizes is None else output_split_sizes
    input_split_sizes = [] if input_split_sizes is None else input_split_sizes

    group = group or _get_default_group()
    work = group.alltoall_base(
        output, input, output_split_sizes, input_split_sizes, opts
    )

    if async_op:
        return work
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()