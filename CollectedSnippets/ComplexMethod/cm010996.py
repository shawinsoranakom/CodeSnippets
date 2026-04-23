def all_reduce_coalesced(tensors, op=ReduceOp.SUM, group=None, async_op: bool = False):
    """
    WARNING: at this time individual shape checking is not implemented across nodes.

    For example, if the rank 0 node passes [torch.rand(4), torch.rand(2)] and the
    rank 1 node passes [torch.rand(2), torch.rand(2), torch.rand(2)], the allreduce
    operation will proceed without complaint and return erroneous outputs. This lack
    of shape checking results in significant performance improvements but users of this
    function should take extra care to ensure that each node passes in tensors whose
    shapes match across nodes.

    Reduces each tensor in tensors (residing on the same device) across all machines
    in such a way that all get the final result.

    After the call each tensor in tensors is going to bitwise identical
    in all processes.

    Complex tensors are supported.

    Args:
        tensors (Union[List[Tensor], Tensor]): Input and output of the collective.
            The function operates in-place.
        op (Optional[ReduceOp]): One of the values from
            ``torch.distributed.ReduceOp`` enum. Specifies an operation used for
            element-wise reductions.
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (Optional[bool]): Whether this op should be an async op.

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group.

    """
    if isinstance(tensors, torch.Tensor):
        tensors = [tensors]
    relevant_args = tuple(tensors) if isinstance(tensors, (list, tuple)) else (tensors,)
    if has_torch_function(relevant_args):
        return handle_torch_function(
            all_reduce_coalesced,
            relevant_args,
            tensors,
            op=op,
            group=group,
            async_op=async_op,
        )

    _check_tensor_list(tensors, "tensor")
    _ensure_all_tensors_same_dtype(tensors)
    if _rank_not_in_group(group):
        _warn_not_in_group("all_reduce_coalesced")
        return

    if any(t.is_complex() for t in tensors) and not supports_complex(op):
        raise ValueError(f"all_reduce does not support {op} on complex tensors")

    tensors = [t if not t.is_complex() else torch.view_as_real(t) for t in tensors]

    opts = AllreduceCoalescedOptions()
    opts.reduceOp = op
    opts.asyncOp = async_op
    group = group or _get_default_group()
    work = group.allreduce_coalesced(tensors, opts)

    if async_op:
        return work.get_future()
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()