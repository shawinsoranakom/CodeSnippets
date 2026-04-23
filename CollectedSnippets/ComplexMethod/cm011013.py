def _destroy_all_other_groups(exclude_group: ProcessGroup | None = None) -> None:
    """
    Destroy all process groups except the excluded group and clean up all global state.

    This is necessary when shrinking the default group because global ranks
    are reassigned by NCCL, making all existing process groups inconsistent.

    Note: Uses abort for non-collective cleanup since excluded ranks may not
    participate in collective operations. Backend cleanup is handled independently per group.

    Args:
        exclude_group (ProcessGroup, optional): Process group to exclude from destruction.
            If None, destroys all process groups.
    """
    # Get list of groups to destroy (avoid modifying dict while iterating)
    groups_to_destroy = []
    for pg in list(_world.pg_group_ranks.keys()):
        if exclude_group is not None and pg == exclude_group:
            continue
        groups_to_destroy.append(pg)

    # Warn user about automatic destruction
    if groups_to_destroy:
        group_names = [_get_process_group_name(pg) for pg in groups_to_destroy]
        logger.warning(
            "Shrinking default group will destroy %d other process groups: %s. "
            "This is necessary because shrinking the default group reassigns global ranks, "
            "making existing groups inconsistent.",
            len(groups_to_destroy),
            ", ".join(group_names),
        )

    # Destroy each group and clean up global state
    for pg in groups_to_destroy:
        try:
            # First call abort_process_group which handles the C++ cleanup non-collectively
            _abort_process_group(pg)
        except Exception:
            # Log but don't fail - some groups might already be destroyed
            logger.warning(
                "Failed to abort process group %s",
                _get_process_group_name(pg),
                exc_info=True,
            )

        # Ensure all global state is cleaned up even if _abort_process_group fails
        # or doesn't clean up everything
        _cleanup_process_group_global_state(pg)