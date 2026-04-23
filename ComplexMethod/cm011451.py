def _context_parallel_buffers(
    mesh: DeviceMesh,
    buffers: list[torch.Tensor | BlockMask],
    buffer_seq_dims: list[int],
    load_balancer: _LoadBalancer | None = None,
) -> list[torch.Tensor | BlockMask]:
    """
    Shard the buffers along the sequence dimensions according to CP rules.
    Args:
        mesh (:class:`DeviceMesh`): the device mesh for the context parallelism.
        buffers (List[torch.Tensor]): the buffers to be sharded.
        seq_dims (List[int]): the sequence dimensions of ``buffers``. This list
            must have the same length as ``buffers``.
        load_balancer (Optional[:class:`_LoadBalancer`]): an optional `_LoadBalancer`
            object. If this argument is `None`, it means the `buffers` need no
            rearrangement before being sharded. If this argument is a `_LoadBalancer`
            object, call its `_generate_indices(restore=False)` to generate the
            rearrangement indices such that each shard of `buffer[rearrange_idx]` is
            well-balanced (i.e., having close sparsities).

    Returns:
        List[torch.Tensor]: the sharded buffers.

    Note:
        For `_context_parallel_shard` we require a non-None `load_balancer` object to be
        explicitly passed if load-balancing is needed.
    """
    # generate the index tensor for rearranging the buffer if a load-balance
    # is available
    load_balance_indices = load_balancer._generate_indices() if load_balancer else None
    if not (load_balance_indices is None or load_balance_indices.ndim == 2):
        raise AssertionError(
            "load balance index expects shape (1, seq_len) or (B, seq_len) "
            f"but got {load_balance_indices.shape}."
        )

    new_buffers = []
    sharded_buffer: torch.Tensor | BlockMask
    for buffer, seq_dim in zip(buffers, buffer_seq_dims):
        if isinstance(buffer, torch.Tensor):
            # NOTE: assuming batch dim is 0

            if load_balance_indices is not None:
                # TODO: we should expclitly ask users to unsqueeze the batch dim.
                # But this is a BC breaking ask.
                # However, what we have done today is also not very safe.
                idx_batch_size = load_balance_indices.size(0)
                data_batch_size = buffer.size(0) if seq_dim > 0 else 1

                if idx_batch_size != 1 and idx_batch_size != data_batch_size:
                    raise ValueError(
                        "Cannot rearrange buffer: "
                        f"load_balance_indices has shape {load_balance_indices.shape}, "
                        f"but buffer has shape {buffer.shape}."
                    )

                if seq_dim == 0:
                    # buffer has shape [seq_len] or [seq_len, ...]
                    # Just use the first (and only) batch of indices
                    buffer = torch.index_select(
                        buffer, dim=0, index=load_balance_indices[0]
                    )
                else:
                    indices = load_balance_indices
                    if idx_batch_size == 1:
                        size = [data_batch_size] + list(indices.size())[1:]
                        indices = indices.expand(*size)

                    # load_balance_indices that has shape [B, seq_len] where:
                    #   - dim 0 corresponds to buffer dim 0 (batch)
                    #   - dim 1 corresponds to buffer dim seq_dim
                    # Need to insert dimensions for all dims between 0 and seq_dim,
                    # and all dims after seq_dim.

                    # Insert dimensions between batch (dim 0) and seq_dim
                    for i in range(1, seq_dim):
                        indices = indices.unsqueeze(i)

                    # Insert dimensions after seq_dim
                    for _ in range(seq_dim + 1, buffer.ndim):
                        indices = indices.unsqueeze(-1)

                    # Expand to match buffer's shape
                    indices = indices.expand(buffer.shape)

                    buffer = torch.gather(buffer, dim=seq_dim, index=indices)

            # use DTensor to shard the buffer on sequence dimension,
            # retain the local tensor
            sharded_buffer = distribute_tensor(
                buffer, mesh, [Shard(seq_dim)], src_data_rank=None
            ).to_local()
        elif isinstance(buffer, BlockMask):
            sharded_buffer = _create_cp_block_mask(
                mask_mod=buffer.mask_mod,
                B=buffer.kv_num_blocks.shape[0],
                H=buffer.kv_num_blocks.shape[1],
                Q_LEN=buffer.seq_lengths[0],
                KV_LEN=buffer.seq_lengths[1],
                device_mesh=mesh,
                load_balancer=load_balancer,
            )
        else:
            raise ValueError(f"Unknown buffer type: {type(buffer)}")

        new_buffers.append(sharded_buffer)

    return new_buffers