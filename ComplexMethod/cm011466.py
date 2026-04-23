def run_torchrec_row_wise_uneven_sharding_example(rank, world_size):
    # row-wise uneven sharding example:
    #   One table is unevenly sharded by rows within the global ProcessGroup.
    #   In our example, the table's num_embedding is 8, and the embedding dim is 16
    #   The global ProcessGroup has 4 ranks, and each rank will have the local shard
    #   of shape:
    #       rank 0: [1, 16]
    #       rank 1: [3, 16]
    #       rank 2: [1, 16]
    #       rank 3: [3, 16]

    # device mesh is a representation of the worker ranks
    # create a 1-D device mesh that includes every rank
    device_type = get_device_type()
    device = torch.device(device_type)
    device_mesh = init_device_mesh(device_type=device_type, mesh_shape=(world_size,))

    # manually create the embedding table's local shards
    num_embeddings = 8
    embedding_dim = 16
    emb_table_shape = torch.Size([num_embeddings, embedding_dim])
    # tensor shape
    local_shard_shape = (
        torch.Size([1, embedding_dim])
        if rank % 2 == 0
        else torch.Size([3, embedding_dim])
    )
    # tensor offset
    local_shard_offset = torch.Size((rank // 2 * 4 + rank % 2 * 1, embedding_dim))
    # tensor
    local_tensor = torch.randn(local_shard_shape, device=device)
    # local shards
    # row-wise sharding: one shard per rank
    # create the local shards wrapper
    # pyrefly: ignore [no-matching-overload]
    local_shards_wrapper = LocalShardsWrapper(
        local_shards=[local_tensor],
        offsets=[local_shard_offset],
    )

    ###########################################################################
    # example 1: transform local_shards into DTensor
    # create the DTensorMetadata which torchrec should provide
    row_wise_sharding_placements: list[Placement] = [Shard(0)]

    # note: for uneven sharding, we need to specify the shape and stride because
    # DTensor would assume even sharding and compute shape/stride based on the
    # assumption. Torchrec needs to pass in this information explicitly.
    # shape/stride are global tensor's shape and stride
    dtensor = DTensor.from_local(
        local_shards_wrapper,  # a torch.Tensor subclass
        device_mesh,  # DeviceMesh
        row_wise_sharding_placements,  # List[Placement]
        run_check=False,
        shape=emb_table_shape,  # this is required for uneven sharding
        stride=(embedding_dim, 1),
    )
    # so far visualize_sharding() cannot print correctly for unevenly sharded DTensor
    # because it relies on offset computation which assumes even sharding.
    visualize_sharding(dtensor, header="Row-wise uneven sharding example in DTensor")
    # check the dtensor has the correct shape and stride on all ranks
    if dtensor.shape != emb_table_shape:
        raise AssertionError
    if dtensor.stride() != (embedding_dim, 1):
        raise AssertionError

    ###########################################################################
    # example 2: transform DTensor into local_shards
    # note: DTensor.to_local() always returns a LocalShardsWrapper
    dtensor_local_shards = dtensor.to_local()
    if not isinstance(dtensor_local_shards, LocalShardsWrapper):
        raise AssertionError
    shard_tensor = dtensor_local_shards.shards[0]
    if not torch.equal(shard_tensor, local_tensor):
        raise AssertionError
    if dtensor_local_shards.shard_sizes[0] != local_shard_shape:  # unwrap shape
        raise AssertionError
    if dtensor_local_shards.shard_offsets[0] != local_shard_offset:  # unwrap offset
        raise AssertionError