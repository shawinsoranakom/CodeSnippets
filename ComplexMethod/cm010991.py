def destroy_process_group(group: ProcessGroup | None = None):
    """
    Destroy a given process group, and deinitialize the distributed package.

    Args:
        group (ProcessGroup, optional): The process group to be destroyed, if
                                        group.WORLD is given, all process
                                        groups including the default one will
                                        be destroyed.
    """
    global _world

    if group == GroupMember.NON_GROUP_MEMBER:
        return

    if group is None:
        pg = GroupMember.WORLD
    else:
        pg = group

    if pg is None:
        raise AssertionError("Process group cannot be None")
    if _world.pg_map.get(pg, None) is None:
        raise ValueError("Invalid process group specified")

    # When users register Python onCompletion hooks, those hooks will run on a
    # different thread than the main thread. Today, the ProcessGroup dtor does
    # wait for that thread. However, the dtor might finish after the Python
    # Interpreter exits. After that grabbing the GIL for the Python hook will crash.
    # We can either revive the interpreter when running hooks or keep the main one
    # alive until all works and hooks are done. The current implementation does the
    # latter. Therefore, we explicitly call _wait_for_pending_works() here to wait
    # for the pending hooks to finish.
    if type(pg) is ProcessGroup and pg._has_hooks():
        pg._wait_for_pending_works()

    if group is None or group == GroupMember.WORLD:
        for comm in _world.comms:
            comm.finalize()
        _world.comms.clear()

        # shutdown all backends in the order of pg names. shutting down in order because
        # ncclCommAbort() was a 'collective' call in some versions of NCCL.
        for pg_to_shutdown in sorted(
            _world.pg_names, key=lambda x: _world.pg_names[x], reverse=True
        ):
            pg_to_shutdown.shutdown()

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
        if _TORCHCOMM_AVAILABLE:
            for device_type in pg._device_types:
                backend = pg._get_backend(device_type)
                if isinstance(backend, _BackendWrapper):
                    backend.get_comm().finalize()
            _world.comms.clear()
        pg.shutdown()
        del _world.pg_map[pg]
        del _world.pg_names[pg]
        del _world.pg_group_ranks[pg]
        del _world.pg_backend_config[pg]
        if pg in _world.pg_coalesce_state:
            warnings.warn(
                "Some coalesced collectives haven't been launched when "
                "ProcessGroup is destroyed. They will be cleaned.",
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