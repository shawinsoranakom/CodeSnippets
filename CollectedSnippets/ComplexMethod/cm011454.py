def context_parallel_unshard(
    mesh: DeviceMesh,
    buffers: list[torch.Tensor],
    seq_dims: list[int],
    load_balancer: _LoadBalancer | None = None,
) -> list[torch.Tensor]:
    """
    Unshard the tensors (e.g., output) that are sharded due to context parallelism.

    Args:
        mesh (:class:`DeviceMesh`): the device mesh for the context parallelism.
        buffers (List[torch.Tensor]): the buffers to be unsharded.
        seq_dims (List[int]): the sequence dimensions of ``buffers``. This list
            must have the same length as ``buffers``.
        load_balancer (Optional[:class:`_Loadbalancer`]): an optional `_LoadBalancer`
            object. If this argument is `None`, it means the `buffers` were not
            rearranged when being sharded and there's no need to put it back to order
            after unsharding. If this argument is a `_LoadBalancer` object, call
            its `_generate_indices(restore=True)` to generate the restore indices such
            that `unsharded[restore_idx]` is the original buffer.

    Returns:
        List[torch.Tensor]: the unsharded buffers.

    Note:
        For `context_parallel_unshard` we require not-None `load_balancer` object be
        explicitly passed if flex_attention() is to be used and load-balancing is needed.
        This is different from the case of SDPA though we strongly suggest users follow
        the same convention.
    """
    device = buffers[0].device
    cp_world_size = mesh.size()
    seq_length = buffers[0].shape[seq_dims[0]] * cp_world_size

    # If users don't pass in a `load_balancer`:
    # - if `enable_load_balance` is True, we use the default round-robin
    #   load balancer.
    # - if `enable_load_balance` is False, we don't do any load balancing
    #   by passing in `None` as `restore_indices`.
    load_balancer = load_balancer or _create_default_load_balancer(
        seq_length, cp_world_size, device
    )
    restore_indices = (
        load_balancer._generate_indices(restore=True) if load_balancer else None
    )

    if not (restore_indices is None or restore_indices.ndim == 2):
        raise AssertionError(
            "load balance restore index expects shape (1, seq_len) or (B, seq_len) "
            f"but got {restore_indices.shape}."
        )
    unsharded_buffers = []
    for b, dim in zip(buffers, seq_dims):
        b = b.contiguous()
        unsharded_b = _maybe_wait(ft_c.all_gather_tensor(b, dim, mesh))

        if restore_indices is not None:
            # NOTE: assuming batch dim is 0
            idx_batch_size = restore_indices.size(0)
            data_batch_size = unsharded_b.size(0)
            if idx_batch_size != 1 and idx_batch_size != data_batch_size:
                raise ValueError(
                    "Cannot restore buffer: "
                    f"restore_indices has shape {restore_indices.shape}, "
                    f"but unsharded_b has shape {unsharded_b.shape}."
                )

            for i in range(data_batch_size):
                index = (
                    restore_indices[0]  # identical load-balance in batch
                    if idx_batch_size == 1
                    else restore_indices[i]
                )
                unsharded_b_batch_i = torch.index_select(
                    unsharded_b[i], dim=dim - 1, index=index
                )
                unsharded_b[i] = unsharded_b_batch_i

        unsharded_buffers.append(unsharded_b)

    return unsharded_buffers