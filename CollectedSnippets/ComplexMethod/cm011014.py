def _cleanup_process_group_global_state(pg: ProcessGroup) -> None:
    """
    Clean up all global state associated with a process group.

    This function ensures complete cleanup of process group state from all
    global dictionaries and registries, even if destroy_process_group fails
    or doesn't clean up everything. This is critical when destroying multiple
    groups to prevent inconsistent state.

    The cleanup removes the process group from:
    - _world.pg_map (backend and store mapping)
    - _world.pg_names (group name mapping)
    - _world.pg_group_ranks (rank mappings)
    - _world.pg_backend_config (backend configuration)
    - _world.tags_to_pg and _world.pg_to_tag (tag mappings)
    - _world.pg_coalesce_state (coalescing state)
    - C++ internal registries via _unregister_process_group

    Args:
        pg (ProcessGroup): The process group to clean up.
    """
    try:
        # Clean up main process group mappings
        _world.pg_map.pop(pg, None)
        _world.pg_group_ranks.pop(pg, None)
        _world.pg_backend_config.pop(pg, None)

        # Clean up process group name mapping
        group_name = _world.pg_names.pop(pg, None)

        # Clean up tag mappings
        pg_tag = _world.pg_to_tag.pop(pg, None)
        if pg_tag is not None and pg_tag in _world.tags_to_pg:
            try:
                _world.tags_to_pg[pg_tag].remove(pg)
                # Remove the tag entry if list is empty
                if not _world.tags_to_pg[pg_tag]:
                    _world.tags_to_pg.pop(pg_tag, None)
            except (ValueError, KeyError):
                # Process group was already removed from the list
                pass

        # Clean up any registered process group names using C++ unregister function
        if group_name is not None:
            try:
                _unregister_process_group(group_name)
            except Exception:
                # Process group name might not be registered or already unregistered
                pass

        # Clean up coalesce state if present
        _world.pg_coalesce_state.pop(pg, None)

    except Exception:
        # Log cleanup failures but don't propagate - we want to continue with other cleanups
        logger.warning(
            "Failed to fully clean up global state for process group", exc_info=True
        )