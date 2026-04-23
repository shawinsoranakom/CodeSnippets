def _rewrite_spec_if_needed(
    spec: shard_spec.ShardingSpec, tensor: torch.Tensor, rank: int
) -> shard_spec.ShardingSpec:
    """
    Rewrite ``spec`` to match the device of ``tensor``.

    FSDP.sharded_optim_state_dict sneakly ships optimizer state to CPU so if the original ShardingSpec
    produces CUDA metadata, ST construction bombs.
    """
    if not isinstance(spec, ChunkShardingSpec):
        return spec

    # let's see if we need
    rewrite = False
    for p in spec.placements:
        p = cast(_remote_device, p)
        if p.rank() == rank and p.device() != tensor.device:
            rewrite = True
            break
    if rewrite:
        spec = copy.deepcopy(spec)
        # pyrefly: ignore [missing-attribute]
        for i, placement in enumerate(spec.placements):
            placement = cast(_remote_device, placement)
            if placement.rank() == rank and placement.device() != tensor.device:
                # pyrefly: ignore [missing-attribute]
                spec.placements[i] = _remote_device(f"rank:{rank}/{tensor.device}")

    return spec