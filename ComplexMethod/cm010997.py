def gather_object(
    obj: Any,
    object_gather_list: list[Any] | None = None,
    dst: int | None = None,
    group: ProcessGroup | None = None,
    group_dst: int | None = None,
):
    """
    Gathers picklable objects from the whole group in a single process.

    Similar to :func:`gather`, but Python objects can be passed in. Note that the
    object must be picklable in order to be gathered.

    Args:
        obj (Any): Input object. Must be picklable.
        object_gather_list (list[Any]): Output list. On the ``dst`` rank, it
            should be correctly sized as the size of the group for this
            collective and will contain the output. Must be ``None`` on non-dst
            ranks. (default is ``None``)
        dst (int, optional): Destination rank on global process group (regardless of ``group`` argument).
            (If both ``dst`` and ``group_dst`` are None, default is global rank 0)
        group: (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used. Default is ``None``.
        group_dst (int, optional): Destination rank on ``group``.  Invalid to specify both ``dst`` and ``group_dst``

    Returns:
        None. On the ``dst`` rank, ``object_gather_list`` will contain the
        output of the collective.

    .. note:: Note that this API differs slightly from the gather collective
        since it does not provide an async_op handle and thus will be a blocking
        call.

    .. note:: For NCCL-based processed groups, internal tensor representations
        of objects must be moved to the GPU device before communication takes
        place. In this case, the device used is given by
        ``torch.cuda.current_device()`` and it is the user's responsibility to
        ensure that this is set so that each rank has an individual GPU, via
        ``torch.cuda.set_device()``.

    .. warning::
        Object collectives have a number of serious performance and scalability
        limitations.  See :ref:`object_collectives` for details.

    .. warning::
        :func:`gather_object` uses ``pickle`` module implicitly, which is
        known to be insecure. It is possible to construct malicious pickle data
        which will execute arbitrary code during unpickling. Only call this
        function with data you trust.

    .. warning::
        Calling :func:`gather_object` with GPU tensors is not well supported
        and inefficient as it incurs GPU -> CPU transfer since tensors would be
        pickled. Please consider using :func:`gather` instead.

    Example::
        >>> # xdoctest: +SKIP("need process group init")
        >>> # Note: Process group initialization omitted on each rank.
        >>> import torch.distributed as dist
        >>> # Assumes world_size of 3.
        >>> gather_objects = ["foo", 12, {1: 2}] # any picklable object
        >>> output = [None for _ in gather_objects]
        >>> dist.gather_object(
        ...     gather_objects[dist.get_rank()],
        ...     output if dist.get_rank() == 0 else None,
        ...     dst=0
        ... )
        >>> # On rank 0
        >>> output
        ['foo', 12, {1: 2}]
    """
    group = _group_or_default_group(group)
    if dst is None and group_dst is None:
        dst = 0
    group_dst = _canonicalize_group_rank(group, dst, group_dst, return_global=False)
    if _rank_not_in_group(group):
        _warn_not_in_group("gather_object")
        return

    # Ensure object_gather_list is specified appropriately.
    my_group_rank = group.rank()
    _validate_output_list_for_rank(my_group_rank, group_dst, object_gather_list)
    current_device = _get_object_coll_device(group)
    input_tensor, local_size = _object_to_tensor(obj, current_device, group)

    # Gather all local sizes. This is so that we can find the max size, and index
    # until the correct size when deserializing the tensors.
    group_size = get_world_size(group=group)
    object_sizes_tensor = torch.zeros(
        group_size, dtype=torch.long, device=current_device
    )
    object_size_list = [
        object_sizes_tensor[i].unsqueeze(dim=0) for i in range(group_size)
    ]
    # Allgather tensor sizes. An all-gather is needed here despite this being a
    # gather, since each rank needs to broadcast a tensor of the same (maximal)
    # size.
    all_gather(object_size_list, local_size, group=group)
    max_object_size = int(max(object_size_list).item())  # type: ignore[type-var]
    # Resize tensor to max size across all ranks.
    input_tensor.resize_(max_object_size)
    # Avoid populating output tensors if the result won't be gathered on this rank.
    if my_group_rank == group_dst:
        coalesced_output_tensor = torch.empty(
            max_object_size * group_size, dtype=torch.uint8, device=current_device
        )
        # Output tensors are nonoverlapping views of coalesced_output_tensor
        output_tensors = [
            coalesced_output_tensor[max_object_size * i : max_object_size * (i + 1)]
            for i in range(group_size)
        ]
    # All ranks call gather with equal-sized tensors.
    gather(
        input_tensor,
        gather_list=output_tensors if my_group_rank == group_dst else None,  # type: ignore[possibly-undefined]
        group_dst=group_dst,
        group=group,
    )
    if my_group_rank != group_dst:
        return

    if object_gather_list is None:
        raise AssertionError("Must provide object_gather_list on dst rank")
    # pyrefly: ignore [unbound-name]
    for i, tensor in enumerate(output_tensors):
        tensor = tensor.type(torch.uint8)
        tensor_size = object_size_list[i]
        object_gather_list[i] = _tensor_to_object(tensor, tensor_size, group)