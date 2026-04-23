def load_sharded_optimizer_state_dict(
    model_state_dict: STATE_DICT_TYPE,
    optimizer_key: str,
    storage_reader: StorageReader,
    planner: LoadPlanner | None = None,
) -> STATE_DICT_TYPE:
    """
    Load a state_dict in conjunction with FSDP sharded optimizer state.

    This is the current recommended way to checkpoint FSDP.
    >>> # xdoctest: +SKIP
    >>> import torch.distributed.checkpoint as dist_cp
    >>> # Save
    >>> model: torch.nn.Model
    >>> optim_params = model.parameters()
    >>> optim = torch.optim.SGD(optim_params, lr=0.01)
    >>> # Save
    >>> with FSDP.state_dict_type(model, StateDictType.SHARDED_STATE_DICT):
    >>>     state_dict = {
    >>>         "optimizer": FSDP.optim_state_dict(model, optim),
    >>>         "model": model.state_dict()
    >>>     }
    >>>     dist_cp.save_state_dict(
    >>>         state_dict=optim_state,
    >>>         storage_writer=dist_cp.FileSystemWriter("checkpoint"),
    >>>         planner=dist_cp.DefaultSavePlanner(),
    >>>     )
    >>>
    >>> # Load
    >>> with FSDP.state_dict_type(model_tp, StateDictType.SHARDED_STATE_DICT):
    >>>     model_state_dict = model_tp.state_dict()
    >>>     checkpoint = {
    >>>         "model": model_state_dict
    >>>     }
    >>>     dist_cp.load_state_dict(
    >>>         state_dict=checkpoint,
    >>>         storage_reader=dist_cp.FileSystemReader(checkpoint_file),
    >>>         planner=dist_cp.DefaultLoadPlanner(),
    >>>     )
    >>>     model.load_state_dict(checkpoint["model_state"])
    >>>
    >>>     optim_state = dist_cp.load_sharded_optimizer_state_dict(
    >>>         model_state_dict,
    >>>         optimizer_key="optimizer",
    >>>         storage_reader=dist_cp.FileSystemReader("checkpoint"),
    >>>     )
    >>>
    >>>     flattened_osd = FSDP.optim_state_dict_to_load(
    >>>        model, optim, optim_state["optimizer"]
    >>>     )
    >>>
    >>>     optim.load_state_dict(flattened_osd)
    """
    metadata = storage_reader.read_metadata()

    layout_specs, dp_pg = _get_state_dict_2d_layout(model_state_dict)
    dp_pg_device_type = dist.distributed_c10d._get_pg_default_device(dp_pg).type
    device_module = _get_device_module(dp_pg_device_type)

    if dp_pg is None:
        placements = []
        for i in range(dist.get_world_size()):
            device_info = _normalize_device_info(
                dp_pg_device_type, i % device_module.device_count()
            )
            placements.append(f"rank:{i}/{device_info}")
        sharding_spec = ChunkShardingSpec(dim=0, placements=placements)  # type: ignore[arg-type]
    else:
        sharding_spec = _create_colwise_spec(dp_pg)

    # Create a state_dict for optimizer state
    state_dict: STATE_DICT_TYPE = {}

    fqn_to_offset: dict[str, Sequence[int]] = {}
    for key, value in metadata.state_dict_metadata.items():
        key_path = metadata.planner_data[key]
        if key_path[0] != optimizer_key:
            continue

        if isinstance(value, BytesStorageMetadata):
            state_dict[key] = "<bytes_io>"
            continue

        # value: TensorStorageMetadata
        if value.size.numel() == 1:
            state_dict[key] = _alloc_tensor(
                value.properties, value.size, dp_pg_device_type
            )
        elif dp_pg is None:
            state_dict[key] = _create_chunk_sharded_tensor(
                _alloc_tensor(value.properties, value.size, dp_pg_device_type),
                rank=dist.get_rank(),
                world_size=dist.get_world_size(),
                num_devices_per_node=device_module.device_count(),
                pg=_get_default_group(),
            )
        else:
            spec_key = key_path[2]
            alloc_size = layout_specs.get(spec_key, (None, value.size))[1]

            properties = ShardTensorProperties(
                dtype=value.properties.dtype,
                layout=value.properties.layout,
                requires_grad=value.properties.requires_grad,
                memory_format=value.properties.memory_format,
                pin_memory=value.properties.pin_memory,
            )

            st_md = sharding_spec.build_metadata(torch.Size(alloc_size), properties)
            local_shards = []
            current_rank = dist.get_rank(dp_pg)
            for shard_md in st_md.shards_metadata:
                if cast(_remote_device, shard_md.placement).rank() != current_rank:
                    continue
                local_shards.append(
                    Shard(
                        tensor=_alloc_tensor(
                            value.properties, shard_md.shard_sizes, dp_pg_device_type
                        ),
                        metadata=shard_md,
                    )
                )

            st = ShardedTensor._init_from_local_shards_and_global_metadata(
                local_shards, st_md, process_group=dp_pg
            )

            if spec_key in layout_specs and layout_specs[spec_key][0] is not None:
                fqn_to_offset[key] = cast(Sequence[int], layout_specs[spec_key][0])

            state_dict[key] = st

    # Whether we unflatten before or after doesn't matter
    load_state_dict(
        state_dict=state_dict,
        storage_reader=storage_reader,
        # FIXME the type of planner is wrong in load_state_dict
        planner=_ReaderWithOffset(fqn_to_offset) if dp_pg is not None else planner,
    )

    state_dict = unflatten_state_dict(state_dict, metadata.planner_data)

    return state_dict