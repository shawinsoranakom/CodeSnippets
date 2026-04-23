def all_gather_coalesced(
    output_tensor_lists, input_tensor_list, group=None, async_op: bool = False
):
    """
    Gathers input tensors from the whole group in a list in a coalesced manner.

    Complex tensors are supported.

    Args:
        output_tensor_lists (list[list[Tensor]]): Output list. It should contain
            correctly-sized tensors to be used for output of the collective.
        input_tensor_list (list[Tensor]): Tensors to be broadcast from
            current process. At least one tensor has to be non empty.
        group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
        async_op (bool, optional): Whether this op should be an async op.

    Returns:
        Async work handle, if async_op is set to True.
        None, if not async_op or if not part of the group

    Example:
        we have 2 process groups, 2 ranks.
        rank 0 passes:
            input_tensor_list = [[[1, 1], [1, 1]], [2], [3, 3]]
            output_tensor_lists =
               [[[[-1, -1], [-1, -1]], [-1], [-1, -1]],
                [[[-1, -1], [-1, -1]], [-1], [-1, -1]]]
        rank 1 passes:
            input_tensor_list = [[[3, 3], [3, 3]], [5], [1, 1]]
            output_tensor_lists =
               [[[[-1, -1], [-1, -1]], [-1], [-1, -1]],
                [[[-1, -1], [-1, -1]], [-1], [-1, -1]]]
        both rank 0 and 1 get:
            output_tensor_lists =
               [[[1, 1], [1, 1]], [2], [3, 3]],
                [[3, 3], [3, 3]], [5], [1, 1]]].

    WARNING: at this time individual shape checking is not implemented across nodes.
    For example, if the rank 0 node passes [torch.rand(4), torch.rand(2)] and the
    rank 1 node passes [torch.rand(2), torch.rand(2), torch.rand(2)], the
    all_gather_coalesced operation will proceed without complaint and return
    erroneous outputs. This lack of shape checking results in significant
    performance improvements but users of this function should take extra care
    to ensure that each node passes in tensors whose shapes match across nodes.
    """
    relevant_args = (
        tuple(input_tensor_list)
        if isinstance(input_tensor_list, (list, tuple))
        else (input_tensor_list,)
    )
    if has_torch_function(relevant_args):
        return handle_torch_function(
            all_gather_coalesced,
            relevant_args,
            output_tensor_lists,
            input_tensor_list,
            group=group,
            async_op=async_op,
        )

    # We only check basic compatibility with C++ params here, C++ code will
    # do shape and type checking.
    if _rank_not_in_group(group):
        _warn_not_in_group("all_gather_coalesced")
        return
    _check_tensor_list(input_tensor_list, "input_tensor_list")
    _ensure_all_tensors_same_dtype(input_tensor_list)
    if not isinstance(output_tensor_lists, list):
        raise TypeError(
            "Invalid function argument: output_tensor_lists should be a list"
        )
    for output_tensor_list in output_tensor_lists:
        _check_tensor_list(output_tensor_list, "output_tensor_lists")
        _ensure_all_tensors_same_dtype(output_tensor_list)

    output_tensor_lists = [
        [t if not t.is_complex() else torch.view_as_real(t) for t in l]
        for l in output_tensor_lists
    ]
    input_tensor_list = [
        t if not t.is_complex() else torch.view_as_real(t) for t in input_tensor_list
    ]

    group = group or _get_default_group()
    opts = AllgatherOptions()
    opts.asyncOp = async_op
    work = group.allgather_coalesced(output_tensor_lists, input_tensor_list, opts)

    if async_op:
        return work.get_future()
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()