def scatter(
    tensor: torch.Tensor,
    scatter_list: list[torch.Tensor] | None = None,
    src: int | None = None,
    group: ProcessGroup | None = None,
    async_op: bool = False,
    group_src: int | None = None,
):
    """
    Scatters a list of tensors to all processes in a group.

    Each process will receive exactly one tensor and store its data in the
    ``tensor`` argument.

    Complex tensors are supported.

    Args:
        tensor (Tensor): Output tensor.
        scatter_list (list[Tensor]): List of tensors to scatter (default is
            None, must be specified on the source rank)
        src (int): Source rank on global process group (regardless of ``group`` argument).
            (If both ``src`` and ``group_src`` are None, default is global rank 0)
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (bool, optional): Whether this op should be an async op
        group_src (int, optional): Source rank on ``group``.  Invalid to specify both ``src`` and ``group_src``

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group

    .. note:: Note that all Tensors in scatter_list must have the same size.

    Example::
        >>> # xdoctest: +SKIP("need process group init")
        >>> # Note: Process group initialization omitted on each rank.
        >>> import torch.distributed as dist
        >>> tensor_size = 2
        >>> device = torch.device(f'cuda:{rank}')
        >>> output_tensor = torch.zeros(tensor_size, device=device)
        >>> if dist.get_rank() == 0:
        >>>     # Assumes world_size of 2.
        >>>     # Only tensors, all of which must be the same size.
        >>>     t_ones = torch.ones(tensor_size, device=device)
        >>>     t_fives = torch.ones(tensor_size, device=device) * 5
        >>>     scatter_list = [t_ones, t_fives]
        >>> else:
        >>>     scatter_list = None
        >>> dist.scatter(output_tensor, scatter_list, src=0)
        >>> # Rank i gets scatter_list[i].
        >>> output_tensor
        tensor([1., 1.], device='cuda:0') # Rank 0
        tensor([5., 5.], device='cuda:1') # Rank 1

    """
    relevant_args = (tensor,)
    if has_torch_function(relevant_args):
        return handle_torch_function(
            scatter,
            relevant_args,
            tensor,
            scatter_list=scatter_list,
            src=src,
            group=group,
            async_op=async_op,
            group_src=group_src,
        )

    _check_single_tensor(tensor, "tensor")
    # Parameter ``scatter_list`` may be left unspecified on non-src ranks.
    if scatter_list:
        _check_tensor_list(scatter_list, "scatter_list")
    else:
        scatter_list = []
    _ensure_all_tensors_same_dtype(tensor, scatter_list)
    group = _group_or_default_group(group)
    if src is None and group_src is None:
        src = 0
    group_src = _canonicalize_group_rank(group, src, group_src, return_global=False)
    if _rank_not_in_group(group):
        _warn_not_in_group("scatter")
        return
    scatter_list = [
        t if not t.is_complex() else torch.view_as_real(t) for t in scatter_list
    ]
    tensor = tensor if not tensor.is_complex() else torch.view_as_real(tensor)

    my_group_rank = group.rank()
    if group_src == my_group_rank:
        if not scatter_list:
            raise ValueError(
                "Argument ``scatter_list`` must be specified on source rank."
            )
        input_tensors = [scatter_list]
        output_tensors = [tensor]
    else:
        if scatter_list:
            raise ValueError(
                "Argument ``scatter_list`` must NOT be specified on non-source ranks."
            )
        input_tensors = []
        output_tensors = [tensor]

    opts = ScatterOptions()
    opts.rootRank = group_src
    opts.asyncOp = async_op
    work = group.scatter(output_tensors, input_tensors, opts)

    if async_op:
        return work
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()