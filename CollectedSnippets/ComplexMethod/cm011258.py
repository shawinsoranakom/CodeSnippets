def _init_from_local_shards(
        cls,
        local_shards: list[Shard],
        *global_size,
        process_group=None,
        init_rrefs=False,
    ):
        # recalc metadata handles special ST creation cases like each rank only has tensor available
        # caller need to provide None on the unknown dimension of the global size
        # We will change None into zeros and go through the same amount of checks as before to create ST
        # and use all_gather to calculate the offsets and global size for metadata
        # It is compatible with the current use case since, conventionally we don't pass None as global size
        # Therefore the old path won't trigger the new feature
        recalc_metadata = False
        for dim in global_size:
            if dim is None:
                recalc_metadata = True
        if recalc_metadata:
            global_size = tuple(
                0 if dim_size is None else dim_size for dim_size in global_size
            )
        # STEP 1: Validate the Shardmetadatas locally
        process_group = cls._normalize_pg(process_group)
        current_rank = dist.get_rank()  # intentional to get global rank
        world_size = dist.get_world_size(process_group)

        local_sharded_tensor_metadata: ShardedTensorMetadata | None = None
        global_tensor_size = _flatten_tensor_size(global_size)

        if len(local_shards) > 0:
            local_sharded_tensor_metadata = build_metadata_from_local_shards(
                local_shards, global_tensor_size, current_rank, process_group
            )

        # STEP 2. Validate metadata across ranks, and build a global sharded tensor
        # metadata by gathering local ShardedTensorMetadata
        gathered_metadatas: list[ShardedTensorMetadata | None] = []
        if world_size > 1:
            gathered_metadatas = [None for _ in range(world_size)]

            dist.all_gather_object(
                gathered_metadatas, local_sharded_tensor_metadata, group=process_group
            )
        else:
            gathered_metadatas = [local_sharded_tensor_metadata]

        global_sharded_tensor_metadata = build_global_metadata(
            gathered_metadatas, recalc_metadata=recalc_metadata
        )
        if recalc_metadata:
            # for recalc use cases, we only support rw for now, limit the blast radius
            # will modify here once we support more sharding type
            if not (
                len(local_shards) > 0
                and len(global_sharded_tensor_metadata.shards_metadata) > current_rank
            ):
                raise AssertionError(
                    f"# for metadata recalculation, local_shards must be larger than 0 "
                    f"actual:{len(local_shards)}, # glb metadata must be greater than any rank id, "
                    f"# metadata:{len(global_sharded_tensor_metadata.shards_metadata)}, rank id:{current_rank}"
                )
            local_md = [
                shard_md
                for shard_md in global_sharded_tensor_metadata.shards_metadata
                if shard_md.placement.rank() == current_rank
            ]
            if len(local_md) != 1:
                raise AssertionError(
                    f"should has and only has one metadata for local rank, actual:{local_md}"
                )
            local_shards[0].metadata = local_md[0]
        tensor_properties = global_sharded_tensor_metadata.tensor_properties

        # STEP 3: Validation done, create the actual ShardedTensor and populate fields
        # prepare initialization
        spec = shard_spec._infer_sharding_spec_from_shards_metadata(
            global_sharded_tensor_metadata.shards_metadata
        )
        sharded_tensor = cls.__new__(
            cls,
            spec,
            global_sharded_tensor_metadata.size,
            dtype=tensor_properties.dtype,
            layout=tensor_properties.layout,
            pin_memory=tensor_properties.pin_memory,
            requires_grad=tensor_properties.requires_grad,
        )
        sharded_tensor._prepare_init(process_group=process_group, init_rrefs=init_rrefs)

        # attach local_shards to the ShardedTensor created
        sharded_tensor._local_shards = local_shards

        # run post initialization, i.e. map registration, rpc initialization
        sharded_tensor._post_init()
        return sharded_tensor