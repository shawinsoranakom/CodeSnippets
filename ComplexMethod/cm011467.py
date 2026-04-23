def run_torchrec_table_wise_sharding_example(rank, world_size):
    # table-wise example:
    #   each rank in the global ProcessGroup holds one different table.
    #   In our example, the table's num_embedding is 8, and the embedding dim is 16
    #   The global ProcessGroup has 4 ranks, so each rank will have one 8 by 16 complete
    #   table as its local shard.

    device_type = get_device_type()
    device = torch.device(device_type)
    # note: without initializing this mesh, the following local_tensor will be put on
    # device cuda:0.
    init_device_mesh(device_type=device_type, mesh_shape=(world_size,))

    # manually create the embedding table's local shards
    num_embeddings = 8
    embedding_dim = 16
    emb_table_shape = torch.Size([num_embeddings, embedding_dim])

    # for table i, if the current rank holds the table, then the local shard is
    # a LocalShardsWrapper containing the tensor; otherwise the local shard is
    # an empty torch.Tensor
    table_to_shards = {}  # map {table_id: local shard of table_id}
    table_to_local_tensor = {}  # map {table_id: local tensor of table_id}
    # create 4 embedding tables and place them on different ranks
    # each rank will hold one complete table, and the dict will store
    # the corresponding local shard.
    for i in range(world_size):
        # tensor
        local_tensor = (
            torch.randn(*emb_table_shape, device=device)
            if rank == i
            else torch.empty(0, device=device)
        )
        table_to_local_tensor[i] = local_tensor
        # tensor offset
        local_shard_offset = torch.Size((0, 0))
        # wrap local shards into a wrapper
        local_shards_wrapper = (
            # pyrefly: ignore [no-matching-overload]
            LocalShardsWrapper(
                local_shards=[local_tensor],
                offsets=[local_shard_offset],
            )
            if rank == i
            else local_tensor
        )
        table_to_shards[i] = local_shards_wrapper

    ###########################################################################
    # example 1: transform local_shards into DTensor
    table_to_dtensor = {}  # same purpose as _model_parallel_name_to_sharded_tensor
    table_wise_sharding_placements = [Replicate()]  # table-wise sharding

    for table_id, local_shards in table_to_shards.items():
        # create a submesh that only contains the rank we place the table
        # note that we cannot use ``init_device_mesh'' to create a submesh
        # so we choose to use the `DeviceMesh` api to directly create a DeviceMesh
        device_submesh = DeviceMesh(
            device_type=device_type,
            mesh=torch.tensor(
                [table_id], dtype=torch.int64
            ),  # table ``table_id`` is placed on rank ``table_id``
        )
        # create a DTensor from the local shard for the current table
        # note: for uneven sharding, we need to specify the shape and stride because
        # DTensor would assume even sharding and compute shape/stride based on the
        # assumption. Torchrec needs to pass in this information explicitly.
        dtensor = DTensor.from_local(
            local_shards,
            device_submesh,
            table_wise_sharding_placements,
            run_check=False,
            shape=emb_table_shape,  # this is required for uneven sharding
            stride=(embedding_dim, 1),
        )
        table_to_dtensor[table_id] = dtensor

    # print each table's sharding
    for table_id, dtensor in table_to_dtensor.items():
        visualize_sharding(
            dtensor,
            header=f"Table-wise sharding example in DTensor for Table {table_id}",
        )
        # check the dtensor has the correct shape and stride on all ranks
        if dtensor.shape != emb_table_shape:
            raise AssertionError
        if dtensor.stride() != (embedding_dim, 1):
            raise AssertionError

    ###########################################################################
    # example 2: transform DTensor into torch.Tensor
    for table_id, local_tensor in table_to_local_tensor.items():
        # important: note that DTensor.to_local() always returns an empty torch.Tensor
        # no matter what was passed to DTensor._local_tensor.
        dtensor_local_shards = table_to_dtensor[table_id].to_local()
        if rank == table_id:
            if not isinstance(dtensor_local_shards, LocalShardsWrapper):
                raise AssertionError
            shard_tensor = dtensor_local_shards.shards[0]
            if not torch.equal(shard_tensor, local_tensor):  # unwrap tensor
                raise AssertionError
            if dtensor_local_shards.shard_sizes[0] != emb_table_shape:  # unwrap shape
                raise AssertionError
            if dtensor_local_shards.shard_offsets[0] != torch.Size(
                (0, 0)
            ):  # unwrap offset
                raise AssertionError
        else:
            if dtensor_local_shards.numel() != 0:
                raise AssertionError