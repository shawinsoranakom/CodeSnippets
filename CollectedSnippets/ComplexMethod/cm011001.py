def all_gather_into_tensor(output_tensor, input_tensor, group=None, async_op=False):
    """
    Gather tensors from all ranks and put them in a single output tensor.

    This function requires all tensors to be the same size on each process.

    Args:
        output_tensor (Tensor): Output tensor to accommodate tensor elements
            from all ranks. It must be correctly sized to have one of the
            following forms:
            (i) a concatenation of all the input tensors along the primary
            dimension; for definition of "concatenation", see ``torch.cat()``;
            (ii) a stack of all the input tensors along the primary dimension;
            for definition of "stack", see ``torch.stack()``.
            Examples below may better explain the supported output forms.
        input_tensor (Tensor): Tensor to be gathered from current rank.
            Different from the ``all_gather`` API, the input tensors in this
            API must have the same size across all ranks.
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (bool, optional): Whether this op should be an async op

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group

    Examples:
        >>> # xdoctest: +SKIP("need process group init")
        >>> # All tensors below are of torch.int64 dtype and on CUDA devices.
        >>> # We have two ranks.
        >>> device = torch.device(f"cuda:{rank}")
        >>> tensor_in = torch.arange(2, dtype=torch.int64, device=device) + 1 + 2 * rank
        >>> tensor_in
        tensor([1, 2], device='cuda:0') # Rank 0
        tensor([3, 4], device='cuda:1') # Rank 1
        >>> # Output in concatenation form
        >>> tensor_out = torch.zeros(world_size * 2, dtype=torch.int64, device=device)
        >>> dist.all_gather_into_tensor(tensor_out, tensor_in)
        >>> tensor_out
        tensor([1, 2, 3, 4], device='cuda:0') # Rank 0
        tensor([1, 2, 3, 4], device='cuda:1') # Rank 1
        >>> # Output in stack form
        >>> tensor_out2 = torch.zeros(world_size, 2, dtype=torch.int64, device=device)
        >>> dist.all_gather_into_tensor(tensor_out2, tensor_in)
        >>> tensor_out2
        tensor([[1, 2],
                [3, 4]], device='cuda:0') # Rank 0
        tensor([[1, 2],
                [3, 4]], device='cuda:1') # Rank 1
    """
    # Dynamo has built-in logic to map legacy distributed ops to functional collectives.
    # Let's redirect to a torch function mode that can mimic this logic outside Dynamo
    # (e.g., non-strict export implements such a torch function mode).
    relevant_args = (input_tensor,)
    if has_torch_function(relevant_args):
        return handle_torch_function(
            all_gather_into_tensor,
            relevant_args,
            output_tensor,
            input_tensor,
            group=group,
            async_op=async_op,
        )

    _check_single_tensor(input_tensor, "input_tensor")
    _check_single_tensor(output_tensor, "output_tensor")
    if _rank_not_in_group(group):
        _warn_not_in_group("all_gather_into_tensor")
        return

    output_tensor = (
        output_tensor
        if not output_tensor.is_complex()
        else torch.view_as_real(output_tensor)
    )
    input_tensor = (
        input_tensor
        if not input_tensor.is_complex()
        else torch.view_as_real(input_tensor)
    )

    opts = AllgatherOptions()
    opts.asyncOp = async_op

    group = group or _get_default_group()

    if group in _world.pg_coalesce_state:
        # We are in coalescing context, do not issue single operation, just append a collective representation
        coll = _CollOp(all_gather_into_tensor, input_tensor, output_tensor)
        _world.pg_coalesce_state[group].append(coll)
        if async_op:
            return _IllegalWork()
        else:
            return None

    work = group._allgather_base(output_tensor, input_tensor, opts)

    if async_op:
        return work
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()