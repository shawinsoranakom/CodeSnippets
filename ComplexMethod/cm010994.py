def broadcast(
    tensor: torch.Tensor,
    src: int | None = None,
    group: ProcessGroup | None = None,
    async_op: bool = False,
    group_src: int | None = None,
):
    """
    Broadcasts the tensor to the whole group.

    ``tensor`` must have the same number of elements in all processes
    participating in the collective.

    Args:
        tensor (Tensor): Data to be sent if ``src`` is the rank of current
            process, and tensor to be used to save received data otherwise.
        src (int): Source rank on global process group (regardless of ``group`` argument).
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (bool, optional): Whether this op should be an async op
        group_src (int): Source rank on ``group``.  Must specify one of ``group_src``
            and ``src`` but not both.

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group

    """
    relevant_args = (tensor,)
    if has_torch_function(relevant_args):
        return handle_torch_function(
            broadcast,
            relevant_args,
            tensor,
            src=src,
            group=group,
            async_op=async_op,
            group_src=group_src,
        )

    group = _group_or_default_group(group)
    group_src = _canonicalize_group_rank(group, src, group_src, return_global=False)
    _check_single_tensor(tensor, "tensor")
    if _rank_not_in_group(group):
        _warn_not_in_group("broadcast")
        return

    opts = BroadcastOptions()
    opts.rootRank = group_src
    opts.rootTensor = 0
    opts.asyncOp = async_op
    sm90_or_more = not (
        tensor.is_cuda and torch.cuda.get_device_capability(tensor.device)[0] >= 9
    )
    if tensor.is_complex():
        tensor = torch.view_as_real(tensor)
    elif _is_fp8(tensor) and not sm90_or_more:
        # FP8 is supported by NCCL on sm90+, use workaround for older GPUs
        tensor = tensor.view(torch.uint8)
    work = group.broadcast([tensor], opts)
    if async_op:
        return work
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()