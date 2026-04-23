def _context_parallel_shard(
    mesh: DeviceMesh,
    buffers: CPBufferContainer,
    seq_dims: CPBufferSeqDims,
    load_balancer: _LoadBalancer | None = None,
) -> list[torch.Tensor | BlockMask]:
    """
    Shard the buffers along the specified sequence dimensions (`seq_dims`), so that each
    rank retains only its corresponding shard according to the provided `mesh`. If a
    `load_balancer` is provided, the buffers will be rearranged by the load balancer
    before sharding to improve load balance. Buffers can be either tensors or `BlockMask`
    objects. If a buffer is a `BlockMask`, its sharding dimension is determined by the
    `BlockMask` implementation, and the corresponding `seq_dim` is ignored.

    Note:
        For `_context_parallel_shard`, a non-None `load_balancer` must be explicitly passed
        if load balancing is required.

    Args:
        mesh (DeviceMesh): The device mesh used for context parallelism.
        buffers (List[torch.Tensor | BlockMask]): Buffers whose usage depends on the sequence
            dimension. Examples include input batches, labels, and positional embedding buffers.
            These buffers must be sharded along the sequence dimension to ensure correctness.
        seq_dims (List[int]): The sequence dimensions for each buffer in `buffers`. Must have
            the same length as `buffers`.
        load_balancer (Optional[_LoadBalancer]): An optional load balancer object. If provided,
            it rearranges the buffers before sharding to achieve better load balance. If not
            provided, no rearrangement is performed.

    Returns:
        List[torch.Tensor | BlockMask]: The sharded buffers, each corresponding to the local
            shard for the current rank.
    """
    # TODO: these global variables are going to bite us someday.
    # We will have to remove them soon.
    # For the new API, we only support the module wrapper mode.
    global _dispatch_mode
    _dispatch_mode = _DispatchMode.MODULE_WRAPPER
    global _cp_options
    if load_balancer is not None:
        _cp_options.enable_load_balance = True
    else:
        _cp_options.enable_load_balance = False

    if len(buffers) != len(seq_dims):
        raise ValueError(
            "`seq_dims` must have the same number of elements as `buffers`."
        )

    flat_buffers, spec = tree_flatten(buffers)
    flat_seq_dims, _ = tree_flatten(seq_dims)
    if len(flat_buffers) != len(flat_seq_dims):
        raise ValueError("`seq_dims` must have the pytree structure as `buffers`.")

    if isinstance(flat_buffers[0], torch.Tensor):
        device = flat_buffers[0].device
    else:
        device = flat_buffers[0].kv_num_blocks.device
    for buffer in flat_buffers:
        if isinstance(buffer, torch.Tensor):
            if device != buffer.device:
                raise AssertionError("All buffers must be on the same device")
        else:
            if device != buffer.kv_num_blocks.device:
                raise AssertionError("All buffers must be on the same device")

    flat_sharded_buffers = _context_parallel_buffers(
        mesh, flat_buffers, flat_seq_dims, load_balancer
    )

    return tree_unflatten(flat_sharded_buffers, spec)