def _init_from_local_shards_and_global_metadata(  # type: ignore[override]
        cls,
        local_shards: list[Shard],
        sharded_tensor_metadata: ShardedTensorMetadata,
        process_group=None,
        init_rrefs=False,
        sharding_spec=None,
    ) -> ShardedTensor:
        """
        Initialize a ShardedTensor with local shards and a global
        ShardedTensorMetadata built on each rank.

        Warning: This API is experimental and subject to change. It does
                 not do cross rank validations, and fully rely on the user
                 for the correctness of sharded_tensor_metadata on each rank
        """
        process_group = cls._normalize_pg(process_group)
        current_rank = dist.get_rank()  # intentional to get global rank

        shards_metadata = sharded_tensor_metadata.shards_metadata

        local_shard_metadatas = []

        # collect local shard metadatas from the global sharded_tensor_metadata
        for shard_metadata in shards_metadata:  # type: ignore[attr-defined]
            rank, local_device = _parse_and_validate_remote_device(
                process_group, shard_metadata.placement
            )

            if current_rank == rank:
                local_shard_metadatas.append(shard_metadata)

        if len(local_shards) != len(local_shard_metadatas):
            raise RuntimeError(
                f"Number of local shards ({len(local_shards)}) does not match number of local "
                f"shards metadata in sharded_tensor_metadata ({len(local_shard_metadatas)}) "
                f"on rank ({current_rank}) "
            )

        shards_metadata = sharded_tensor_metadata.shards_metadata
        tensor_properties = sharded_tensor_metadata.tensor_properties

        if len(shards_metadata) == 0:
            raise ValueError("shards_metadata must not be empty!")

        if tensor_properties.layout != torch.strided:
            raise ValueError("Only torch.strided layout is currently supported")

        if sharding_spec is None:
            spec = shard_spec._infer_sharding_spec_from_shards_metadata(shards_metadata)
        else:
            spec = sharding_spec

        sharded_tensor = ShardedTensor.__new__(
            ShardedTensor,
            spec,
            sharded_tensor_metadata.size,
            dtype=tensor_properties.dtype,
            layout=tensor_properties.layout,
            pin_memory=tensor_properties.pin_memory,
            requires_grad=tensor_properties.requires_grad,
        )

        def _raise_if_mismatch(expected, actual, prop_name, rank, is_property=False):
            tensor_property_or_metadata = (
                "tensor property" if is_property else "local ShardMetadata"
            )
            if expected != actual:
                raise ValueError(
                    f"Local shards' tensor {prop_name} property is incompatible with "
                    f"{tensor_property_or_metadata} on rank {rank}: "
                    f"{tensor_property_or_metadata} {prop_name}={expected}, "
                    f"local shard tensor {prop_name}={actual}."
                )

        for shard in local_shards:
            shard_meta = shard.metadata
            local_shard_tensor = shard.tensor
            placement = shard_meta.placement
            if placement is None:
                raise AssertionError("Must specify placement for `Shard`!")
            rank = placement.rank()
            local_device = placement.device()

            _raise_if_mismatch(
                tensor_properties.layout,
                local_shard_tensor.layout,
                "layout",
                rank,
                True,
            )
            if not local_shard_tensor.is_contiguous():
                raise ValueError(
                    "Only torch.contiguous_format memory_format is currently supported"
                )

            _raise_if_mismatch(
                shard_meta.shard_sizes,
                list(local_shard_tensor.size()),
                "size",
                rank,
            )
            _raise_if_mismatch(
                tensor_properties.pin_memory,
                local_shard_tensor.is_pinned(),
                "pin_memory",
                rank,
                True,
            )
            _raise_if_mismatch(local_device, local_shard_tensor.device, "device", rank)
            _raise_if_mismatch(
                tensor_properties.dtype,
                local_shard_tensor.dtype,
                "dtype",
                rank,
                True,
            )
            _raise_if_mismatch(
                tensor_properties.requires_grad,
                local_shard_tensor.requires_grad,
                "requires_grad",
                rank,
                True,
            )

        # check if shards_metadata have overlap shards
        validate_non_overlapping_shards_metadata(shards_metadata)

        # check if the shards_metadata is compatible with overall size of the sharded tensor.
        check_tensor(shards_metadata, list(sharded_tensor_metadata.size))

        # done validation, add local_shards
        sharded_tensor._local_shards = local_shards
        sharded_tensor._prepare_init(process_group=process_group, init_rrefs=init_rrefs)

        # run post initialization, i.e. map registration, rpc initialization
        sharded_tensor._post_init()
        return sharded_tensor