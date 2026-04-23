def _pipelined_multi_all_gather_and_consume(
    shard: list[torch.Tensor],
    shard_consumer: Callable[[list[torch.Tensor], int], None],
    ag_out: list[torch.Tensor],
    group_name: c10d.GroupName,
    ag_out_needed: bool = True,
) -> None:
    """
    Perform the following logic with micro-pipelined computation and
    communication:

        gathered = [
            all_gather_tensor(x, gather_dim=0, group=group)
            for x in shard
        ]

        shards = [[] for _ in range(group_size)]
        for x in ag_out:
            for i, y in enumerate(x.chunk(group_size)):
                shards[i].append(y)

        for src_rank, shard in enumerate(shards):
            shard_consumer(shard, src_rank)
    """
    p2p_workspace_size_req = 0
    for x in shard:
        p2p_workspace_size_req += x.numel() * x.element_size()
    symm_mem = get_symm_mem_workspace(group_name, min_size=p2p_workspace_size_req)
    group_size = symm_mem.world_size
    rank = symm_mem.rank

    symm_mem.barrier(channel=0)
    backend_stream = _get_backend_stream()
    backend_stream.wait_stream(torch.cuda.current_stream())

    for x, y in zip(shard, ag_out):
        if not x.is_contiguous():
            raise AssertionError(
                "_pipelined_all_gather_and_consume: all tensors "
                "in `shard` must be contiguous"
            )
        if not y.is_contiguous():
            raise AssertionError(
                "_pipelined_all_gather_and_consume: all tensors "
                "in `ag_out` must be contiguous"
            )
        if x.shape[0] * group_size != y.shape[0]:
            raise AssertionError
        if x.shape[1:] != y.shape[1:]:
            raise AssertionError

    def copy_shard(dst: list[torch.Tensor], src: list[torch.Tensor]) -> None:
        for d, s in zip(dst, src):
            d.copy_(s)

    def get_p2p_bufs(remote_rank: int) -> list[torch.Tensor]:
        offset_bytes = 0
        bufs = []
        for x in shard:
            buf = symm_mem.get_buffer(
                remote_rank,
                x.shape,
                x.dtype,
                storage_offset=offset_bytes // x.element_size(),
            )
            bufs.append(buf)
            offset_bytes += buf.numel() * buf.element_size()
        return bufs

    local_p2p_bufs = get_p2p_bufs(rank)

    # shards[i] => shard from rank i
    shards: list[list[torch.Tensor]] = [[] for _ in range(group_size)]
    for x in ag_out:
        for i, y in enumerate(x.chunk(group_size)):
            shards[i].append(y)

    # Parallelization strategy: after each rank copies its shard into its local
    # p2p buffer, every rank issues independent p2p copy -> shard_consumer
    # sequences to two streams. In addition to computation/communication
    # overlapping, the strategy allows for computation/computation overlapping,
    # greatly reducing quantization inefficiency.
    #
    # Notation:
    # - "mv" for the copy to local buffer
    # - "cp" for p2p copies
    # - "b" for barriers
    #
    # Constraints:
    # - The GPU scheduler may or may not overlap "mv" with the first shard_consumer.
    # - "cp" from different streams cannot overlap.
    #
    # Ideal scenario 0 - "mv" overlaps with the first shard_consumer:
    #
    # stream 0: [ shard_consumer ][ cp ][ shard_consumer ]
    # stream 1: [ mv ][b][ cp ][ shard_consumer ]
    #
    # Ideal scenario 1 - "mv" is scheduled before the first shard_consumer:
    #
    # stream 0:       [ shard_consumer ][ cp ][ shard_consumer ]
    # stream 1: [ mv ][b][ cp ][ shard_consumer ]
    #
    # Suboptimal scenario 0 - "mv" is scheduled after the first shard_consumer:
    #
    # stream 0: [ shard_consumer ]               [ cp ][ shard_consumer ]
    # stream 1:                   [ mv ][b][ cp ][ shard_consumer ]
    #
    # Suboptimal scenario 0 - "b" is scheduled after the first shard_consumer:
    #
    # stream 0:       [ shard_consumer ]         [ cp ][ shard_consumer ]
    # stream 1: [ mv ]                  [b][ cp ][ shard_consumer ]
    #
    # We haven't yet figured out a way to ensure "mv" and "b" are either
    # overlapped with or scheduled before the first shard_consumer. Thus, to
    # prevent suboptimal scenarios, we are giving up the chance to overlap "mv"
    # and "b" with the first shard_consumer for now.
    copy_shard(dst=local_p2p_bufs, src=shard)
    symm_mem.barrier(channel=1)
    backend_stream.wait_stream(torch.cuda.current_stream())

    # At this point, all ranks have copied their local shard to
    # their local p2p buffer. Each rank can now copy and consume
    # remote shards.
    shard_consumer(shard, rank)

    for step in range(1, group_size):
        if step % 2 == 0:
            stream = torch.cuda.current_stream()
        else:
            stream = backend_stream
        remote_rank = (step + rank) % group_size
        remote_p2p_bufs = get_p2p_bufs(remote_rank)
        with stream:
            copy_shard(dst=shards[remote_rank], src=remote_p2p_bufs)
            shard_consumer(shards[remote_rank], remote_rank)

    if ag_out_needed:
        # Copy from input to the all-gather output. Opportunistically overlap
        # it with the last shard_consumer.
        if group_size % 2 == 0:
            stream = torch.cuda.current_stream()
        else:
            stream = backend_stream
        with stream:
            copy_shard(dst=shards[rank], src=shard)

    torch.cuda.current_stream().wait_stream(backend_stream)
    symm_mem.barrier(channel=0)