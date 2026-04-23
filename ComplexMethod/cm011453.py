def context_parallel(
    mesh: DeviceMesh,
    *,
    buffers: list[torch.Tensor] | None = None,
    buffer_seq_dims: list[int] | None = None,
    no_restore_buffers: set[torch.Tensor] | None = None,
) -> Generator[None, None, None]:
    """

    ``context_parallel`` is an experimental API to enable context
    parallelism (CP). This API performs two actions: 1) patch the SDPA
    (``torch.nn.functional.scaled_dot_product_attention``) with the CP-enabled
    one, 2) shard ``buffers`` along the sequence dimension and each rank will
    preserve the corresponding shard according ``mesh``.

    Args:
        mesh (:class:`DeviceMesh`): the device mesh for the context parallelism.
        buffers (Optional[List[torch.Tensor]]): buffers that the usage depend
            on the sequence dimension. Examples are input batch, labels and
            positional embedding buffers. These buffers must be sharded along
            the sequence dimension to ensure the accuracy. The sharding will
            happen in-place, the buffer's shape will change within the context.
            The buffers will be restored after the context finishes.
            ``no_restore_buffers`` can be used to specify which buffers don't
            need to be restored. Note that ``buffers`` should not contain any
            nn.Parameter.
        buffer_seq_dims (Optional[List[int]]): the sequence dimensions of ``buffers``.
        no_restore_buffers (Optional[Set[torch.Tensor]]): buffers in these set
            won't be restored after the context exits. This set must be a subset
            of ``buffers``. If the buffers won't be used after the context exits,
            these buffers can be put in this list to avoid extra restore time.

    .. warning::
        `torch.distributed.tensor.experimental.context_parallel` is a
        prototype feature in PyTorch. The API is subject to change.
    """
    # For the legacy API, we only support the monkey-patch mode.
    # We will deprecate this API once the new API is widely used.
    global _dispatch_mode
    _dispatch_mode = _DispatchMode.MONKEY_PATCH

    buffers = [] if buffers is None else buffers
    buffer_seq_dims = [] if buffer_seq_dims is None else buffer_seq_dims
    no_restore_buffers = set() if no_restore_buffers is None else no_restore_buffers

    if len(buffers) != len(buffer_seq_dims):
        raise ValueError(
            "`seq_dims` must have the same number of elements as `buffers`."
        )

    for buffer in no_restore_buffers:
        # Cannot use `if not buffer in buffers` which will incur tensor comparison.
        if not any(b is buffer for b in buffers):
            raise ValueError("`no_restore_buffers` must be a subset of `buffers`.")

    original_buffers = [None if b in no_restore_buffers else b.clone() for b in buffers]

    device = buffers[0].device
    seq_length = buffers[0].shape[buffer_seq_dims[0]]
    cp_world_size = mesh.size()

    # If `enable_load_balance` is True, the default Head-tail load balancer
    # (:class:`_HeadTailLoadBalancer`) is used to rearrange the buffers before
    # sharding. Otherwise, we don't do any load-balance rearrange by passing
    # `None` to `_context_parallel_shard()`.
    load_balancer = _create_default_load_balancer(seq_length, cp_world_size, device)
    shards = _context_parallel_buffers(
        mesh,
        cast(list[torch.Tensor | BlockMask], buffers),
        buffer_seq_dims,
        load_balancer,
    )
    for buffer, shard in zip(buffers, shards):
        if not isinstance(shard, torch.Tensor):
            raise AssertionError("ContextParallel only supports Tensor")
        shard = shard.clone()
        buffer.resize_(shard.shape)
        buffer.copy_(shard)

    _enable_context_parallel_dispatcher_impl(seq_dim=2, mesh=mesh)
    yield
    _disable_context_parallel_dispatcher_impl()

    for buffer, original_buffer in zip(buffers, original_buffers):
        if original_buffer is not None:
            buffer.resize_(original_buffer.shape)
            buffer.copy_(original_buffer)