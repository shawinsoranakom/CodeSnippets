def _abort_process_group(group: ProcessGroup | None = None):
    """
    Abort a given process group. If group.WORLD (i.e. `None`) is given, all
    process groups including the default one will be aborted.

    Args:
        group (ProcessGroup, optional): The process group to be aborted.

    .. note:: this API is experimental and currently only works with the NCCL
        backend.

    .. note:: this API should be used with `TORCH_NCCL_ASYNC_ERROR_HANDLING`
        turned off (i.e. set to 0). Otherwise, ProcessGroupNCCL's watchdog may
        automatically handle errors or timeouts for you including aborting the
        ProcessGroup.
    """
    global _world

    if group == GroupMember.NON_GROUP_MEMBER:
        return

    pg = group or GroupMember.WORLD

    if pg is None:
        raise AssertionError("Process group cannot be None")
    if _world.pg_map.get(pg, None) is None:
        raise ValueError("Invalid process group specified or has been destroyed.")

    try:
        backend = pg._get_backend(torch.device("cuda"))
    except RuntimeError:
        backend = None

    if group is None or group == GroupMember.WORLD:
        # Abort all backends within a ncclGroupStart|End semantic.
        # This ensures that different NCCL communicators' abort calls won't
        # deadlock each other.
        # For details, please see: https://github.com/pytorch/pytorch/issues/119797
        if is_nccl_available() and isinstance(backend, ProcessGroupNCCL):
            backend._group_start()
        for pg_to_abort in sorted(
            _world.pg_names, key=lambda x: _world.pg_names[x], reverse=True
        ):
            pg_to_abort.abort()
        if is_nccl_available() and isinstance(backend, ProcessGroupNCCL):
            backend._group_end()

        _update_default_pg(None)
        _world.pg_map.clear()
        _world.pg_names.clear()
        _world.pg_group_ranks.clear()
        _world.pg_backend_config.clear()
        _world.pg_to_tag.clear()
        _world.tags_to_pg.clear()
        _world.pg_coalesce_state.clear()
        _unregister_all_process_groups()

        # when process group doesn't have an explicit name (only WORLD (default)
        # process group can have an explicit name), we use global _world.group_count
        # to generate the name. We need to reset the counter on destruction to
        # allow consistent value to be generated when we re-create process
        # groups after some trainers recover from failure
        #
        # We only reset this when WORLD is being destroyed because if this
        # process group is in good state, we aren't dealing with failures.
        _world.group_count = 0
    else:
        pg.abort()
        del _world.pg_map[pg]
        del _world.pg_names[pg]
        del _world.pg_group_ranks[pg]
        del _world.pg_backend_config[pg]
        if pg in _world.pg_coalesce_state:
            warnings.warn(
                "Some coalesced collectives haven't been launched when "
                "ProcessGroup is aborted. They will be cleaned.",
                stacklevel=2,
            )
            del _world.pg_coalesce_state[pg]

        tag = _world.pg_to_tag.get(pg)
        del _world.pg_to_tag[pg]
        if tag is not None:
            try:
                _world.tags_to_pg[tag].remove(pg)
                if tag.startswith("ptd:"):
                    _world.tags_to_pg[""].remove(pg)
            except Exception:
                pass
        _unregister_process_group(pg.group_name)