def split_group(
    parent_pg: ProcessGroup | None = None,
    split_ranks: list | None = None,
    timeout: timedelta | None = None,
    pg_options: Any | None = None,
    group_desc: str | None = None,
) -> ProcessGroup | None:
    """
    Create a new process group split from the given parent process group.

    warning:: This is an experimental API. Only the ``NCCL`` and custom plugin backends
    are supported. Other backends will raise an error.
    Users of this API must guarantee that all ranks in the parent group enter this API call,
    and the split of the sub groups is the same across all ranks in the parent group.

    Args:
        parent_pg (ProcessGroup, optional): The parent process group. If None,
            the default process group will be used. Users need to guarantee that
            the parent group is fully initialized (e.g, communicators are initialized)
        split_ranks (list[list[int]]): the split ranks, which is a list of list of ranks.
            Users need to make sure the validity of the split ranks such that one
            split (represented by one inner list of ints) does not overlap with any other split.
            Note that the ranks in each split is the group rank (instead of global rank)
            in the parent pg. For example, if the parent group has 4 ranks, and split_ranks can be
            [[0, 1], [2, 3]]. Note [[0,1]] is also a valid split, in which case ranks 2, 3 would
            return a non-group member.
        timeout (timedelta, optional): see `init_process_group` for details and default value.
        pg_options (ProcessGroupOptions, optional): Additional options need to be passed in during
            the construction of specific process groups. i.e.``is_high_priority_stream``
            can be specified so that process group can pick up high priority cuda streams.
        group_desc (str, optional): a string to describe the process group.

    Returns:
        ProcessGroup if the current rank is within one split/subgroup given by split_ranks,
        or None if the current rank is not part of any split_ranks`.

    """
    # check inputs
    if split_ranks is None or len(split_ranks) == 0:
        raise ValueError("split_ranks cannot be None or empty")

    global _world
    default_pg = _get_default_group()
    device_id = default_pg.bound_device_id
    if not device_id and not _use_torchcomms_enabled():
        raise RuntimeError(
            "No device associated with the default pg, not safe to split any process groups"
        )
    global_rank = default_pg.rank()
    global_world_size = default_pg.size()

    if not parent_pg:
        parent_pg = default_pg
    if parent_pg not in _world.pg_group_ranks:
        raise ValueError(f"Group {parent_pg} is not registered")

    parent_global_to_group_ranks = _world.pg_group_ranks[parent_pg]
    parent_group_to_global_ranks = {
        group_rank: global_rank
        for global_rank, group_rank in parent_global_to_group_ranks.items()
    }

    if global_rank not in parent_global_to_group_ranks:
        raise ValueError(
            f"Global rank {global_rank} is not part of the parent group {parent_pg}"
        )

    parent_group_rank = parent_global_to_group_ranks[global_rank]

    if torch.accelerator.is_available():
        parent_backend = parent_pg._get_backend(
            torch.accelerator.current_accelerator()  # pyrefly: ignore[bad-argument-type]
        )
    else:
        raise RuntimeError(
            "No backend for the parent process group or its backend does not support splitting"
        )

    # if the parent backend does not support splitting, raise error
    # currently this API only support NCCL and XCCL backend
    if (
        not parent_backend or not parent_backend.supports_splitting
    ) and not _use_torchcomms_enabled():
        raise RuntimeError(
            "No backend for the parent process group or its backend does not support splitting"
        )

    # set the group_desc before the color or no_cloor split
    if hasattr(parent_backend, "comm_split_count") and group_desc is None:
        group_desc = f"{parent_pg.group_desc}:split:{parent_backend.comm_split_count()}"  # type: ignore[attr-defined]

    parent_backend_str, _ = _world.pg_map[parent_pg]
    # same type of backend as the parent process group
    backend = Backend(parent_backend_str)
    backend_config = BackendConfig(backend)

    # TODO: figure out pg option for torchComms
    if pg_options is None and not _use_torchcomms_enabled():
        # default pg_options same as the parent process group
        # A deep copy is needed because if the option will be modified inside split
        # and if we split parent pg multiple times, we will run into device out of bound error.
        pg_options = copy.deepcopy(parent_backend.options)

    # this timeout defaulting/validation is used for all the new_groups/new_subgroups variants,
    # which may just pass their timeout value (or None)
    if timeout is None:
        timeout = _get_default_timeout(backend)
    _check_valid_timeout(timeout)

    # find my group of ranks and my group local rank in split_ranks
    # for ranks which are not in any split PGs, we just pass in this the first split group
    # and None will be returned.
    my_group = split_ranks[0]

    for split_group in split_ranks:
        if len(split_group) == 0:
            raise ValueError("the split group cannot be empty")
        if len(split_group) > global_world_size:
            raise ValueError(
                "the split group's size should be less or equal to the world_size set by init_process_group"
            )
        if len(split_group) != len(set(split_group)):
            raise ValueError("the split group cannot have duplicate ranks")
        split_group = sorted(split_group)
        if parent_group_rank in split_group:
            my_group = split_group
            break

    # use_hashed_name is True to ensure that subgroups have unique names.
    # This is needed as some backends (e.g. Gloo) use the group name as a
    # PrefixStore prefix for initialization of splits. Thus, names have to be
    # unique to avoid key collisions.
    group_name = _process_group_name(my_group, use_hashed_name=True)
    split_pg = parent_pg.split_group(
        my_group,
        timeout=timeout,
        opts=pg_options,
        group_name=group_name,
        group_desc=group_desc,
    )
    if split_pg is None:
        return None

    global_ranks_in_my_group = [parent_group_to_global_ranks[rank] for rank in my_group]
    split_pg.bound_device_id = device_id  # type: ignore[union-attr]

    if torch.accelerator.is_available():
        split_backend_class = split_pg._get_backend(
            torch.accelerator.current_accelerator()  # pyrefly: ignore[bad-argument-type]
        )
    else:
        raise RuntimeError(
            "No backend for the parent process group or its backend does not support splitting"
        )

    if not _use_torchcomms_enabled():
        split_backend_class._set_sequence_number_for_group()
    if split_pg.group_name != group_name:
        raise AssertionError(
            f"group name should be set to {group_name} but got {split_pg.group_name}"
        )

    # update global state
    _world.pg_map[split_pg] = (backend, split_pg.get_group_store())
    _world.pg_names[split_pg] = group_name
    _register_process_group(group_name, split_pg)
    _world.pg_backend_config[split_pg] = str(backend_config)
    pg_tag = f"ptd:{group_name}"
    _world.tags_to_pg.setdefault(pg_tag, []).append(split_pg)
    _world.pg_to_tag[split_pg] = pg_tag

    # Create the global rank to group rank mapping
    _world.pg_group_ranks[split_pg] = {
        global_rank: group_rank
        for group_rank, global_rank in enumerate(global_ranks_in_my_group)
    }

    if _use_torchcomms_enabled():
        # pyrefly: ignore [missing-attribute]
        _world.comms.append(split_backend_class.get_comm())
    return split_pg