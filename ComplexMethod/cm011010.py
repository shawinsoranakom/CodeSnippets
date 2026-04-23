def _new_group_with_tag(
    ranks=None,
    timeout=None,
    backend=None,
    backend_options=None,
    pg_tag=None,
    use_local_synchronization=False,
    group_desc=None,
    device_id: torch.device | None = None,
    sort_ranks: bool = True,
):
    """
    Variant of ``new_group`` that exposes tag creation.

    :: N.B. The mechanism is experimental and tied to the functional collectives effort, see
    ``torch.distributed._functional_collectives`` for reference on how to use it.
    """
    global _world

    default_pg = _get_default_group()
    if device_id is None:
        device_id = default_pg.bound_device_id
    elif default_pg.bound_device_id is not None:
        if device_id != default_pg.bound_device_id:
            raise AssertionError(
                "Mismatched bound device between new pg and the default pg."
            )
    default_backend, default_store = _world.pg_map[default_pg]
    global_rank = default_pg.rank()
    global_world_size = default_pg.size()

    # Default to the same backend as the global process group
    # if the backend is not specified.
    if not backend:
        backend = default_backend
    backend = Backend(backend)

    # this timeout defaulting/validation is used for all the new_groups/new_subgroups variants,
    # which may just pass their timeout value (or None)
    if timeout is None:
        timeout = _get_default_timeout(backend)
    _check_valid_timeout(timeout)

    if use_local_synchronization:
        # MPI backend doesn't have have a way for us to perform a partial sync
        if backend == Backend.MPI:
            raise ValueError(
                "MPI backend doesn't support use_local_synchronization=True"
            )
        if ranks is not None and get_rank() not in ranks:
            return None

    # checks the input ranks
    if ranks is not None:
        if sort_ranks:
            ranks = sorted(ranks)
        if len(set(ranks)) != len(ranks):
            raise ValueError(
                f"ranks list must not contain duplicate entries, got {ranks}"
            )
        group_world_size = len(ranks)
        if group_world_size > global_world_size:
            raise ValueError(
                "the new group's world size should be less or "
                "equal to the world size set by "
                "init_process_group"
            )
        # check ranks' sanity
        for rank in ranks:
            if rank < 0 or rank >= global_world_size:
                raise ValueError(
                    f"Rank {rank} is out of range. Valid ranks are 0 to {global_world_size - 1} "
                    f"(world_size={global_world_size})"
                )
        if global_rank in ranks:
            group_rank = ranks.index(global_rank)
        else:
            group_rank = None
    else:
        ranks = list(range(global_world_size))
        group_world_size = global_world_size
        group_rank = global_rank

    group_name = _process_group_name(ranks, use_hashed_name=use_local_synchronization)

    pg, pg_store = _new_process_group_helper(
        group_world_size,
        group_rank,
        ranks,
        backend,
        default_store,
        group_name,
        backend_options=backend_options,
        timeout=timeout,
        pg_tag=pg_tag,
        device_id=device_id,
        group_desc=group_desc,
    )

    # Create the global rank to group rank mapping
    _world.pg_group_ranks[pg] = {
        global_rank: group_rank for group_rank, global_rank in enumerate(ranks)
    }

    if _is_barrier_after_init() == 1:
        # barrier at the end to ensure that once we return from this method, all
        # process groups including global variables (if any) are updated
        # correctly on all ranks.
        # Update 04/2023: for large-scale runs, this barrier (esp. store-based
        # barrier) may be costly and/or unscalable. Also, in a lot of cases,
        # these barriers may be unnecessary, as proven by a green CI after
        # removal. An environment variable `TORCH_DIST_INIT_BARRIER` has been
        # added which enables this barrier only when set to 1.
        logger.info(
            "Performing barrier after ProcessGroup initialization since "
            "TORCH_DIST_INIT_BARRIER = 1"
        )
        if backend == Backend.MPI:
            # MPI doesn't have store.
            barrier()
        else:
            barrier_store = pg_store if use_local_synchronization else default_store
            world_size = len(ranks) if use_local_synchronization else get_world_size()
            # Use store based barrier here since barrier() used a bunch of
            # default devices and messes up NCCL internal state.
            _store_based_barrier(
                global_rank, barrier_store, group_name, world_size, timeout
            )

    return pg