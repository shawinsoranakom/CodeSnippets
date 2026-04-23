def gather(
    tensor: torch.Tensor,
    gather_list: list[torch.Tensor] | None = None,
    dst: int | None = None,
    group: ProcessGroup | None = None,
    async_op: bool = False,
    group_dst: int | None = None,
):
    """
    Gathers a list of tensors in a single process.

    This function requires all tensors to be the same size on each process.

    Args:
        tensor (Tensor): Input tensor.
        gather_list (list[Tensor], optional): List of appropriately,
            same-sized tensors to use for gathered data
            (default is None, must be specified on the destination rank)
        dst (int, optional): Destination rank on global process group (regardless of ``group`` argument).
            (If both ``dst`` and ``group_dst`` are None, default is global rank 0)
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (bool, optional): Whether this op should be an async op
        group_dst (int, optional): Destination rank on ``group``.  Invalid to specify both ``dst`` and ``group_dst``

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group

    .. note:: Note that all Tensors in gather_list must have the same size.

    Example::
        >>> # xdoctest: +SKIP("no rank")
        >>> # We have 2 process groups, 2 ranks.
        >>> tensor_size = 2
        >>> device = torch.device(f'cuda:{rank}')
        >>> tensor = torch.ones(tensor_size, device=device) + rank
        >>> if dist.get_rank() == 0:
        >>>     gather_list = [torch.zeros_like(tensor, device=device) for i in range(2)]
        >>> else:
        >>>     gather_list = None
        >>> dist.gather(tensor, gather_list, dst=0)
        >>> # Rank 0 gets gathered data.
        >>> gather_list
        [tensor([1., 1.], device='cuda:0'), tensor([2., 2.], device='cuda:0')] # Rank 0
        None                                                                   # Rank 1

    """
    relevant_args = (tensor,)
    if has_torch_function(relevant_args):
        return handle_torch_function(
            gather,
            relevant_args,
            tensor,
            gather_list=gather_list,
            dst=dst,
            group=group,
            async_op=async_op,
            group_dst=group_dst,
        )

    _check_single_tensor(tensor, "tensor")

    # Parameter ``gather_list`` may be left unspecified on non-dst ranks.
    if gather_list:
        _check_tensor_list(gather_list, "gather_list")
    else:
        gather_list = []
    _ensure_all_tensors_same_dtype(tensor, gather_list)
    group = _group_or_default_group(group)
    if _rank_not_in_group(group):
        _warn_not_in_group("gather")
        return
    if dst is None and group_dst is None:
        dst = 0
    group_dst = _canonicalize_group_rank(group, dst, group_dst, return_global=False)
    my_group_rank = group.rank()
    _validate_output_list_for_rank(my_group_rank, group_dst, gather_list)
    output_tensors = [gather_list] if group_dst == my_group_rank else []
    input_tensors = [tensor]

    opts = GatherOptions()
    opts.rootRank = group_dst
    opts.asyncOp = async_op
    work = group.gather(output_tensors, input_tensors, opts)

    if async_op:
        return work
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()