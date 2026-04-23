def _autotune_remote_nodes(
    scheduler: torch._inductor.scheduler.Scheduler,
    choices_by_index: Sequence[_SerializedChoice],
) -> None:
    """
    Go through the nodes in the scheduler and autotune the nodes that were
    autotuned on remote ranks.
    """

    for i, node in enumerate(scheduler.nodes):
        if isinstance(node, SchedulerNode) and isinstance(
            (dist_node := node.node), _DistributedAutotuneBuffer
        ):
            assert dist_node.origin_node is not None
            info = dist_node.origin_node.meta[_DISTRIBUTED_AUTOTUNE_KEY]
            out_tensorbox = dist_node.autotune(choices_by_index[info.index])

            out_storage = out_tensorbox.data
            assert isinstance(out_storage, StorageBox)
            out_buffer = out_storage.data
            assert isinstance(out_buffer, OperationBuffer)

            assert out_buffer.layout == dist_node.layout

            scheduler._replace_node(out_buffer, dist_node, i, node)