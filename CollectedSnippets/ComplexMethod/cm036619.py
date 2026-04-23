def assert_executor(executor, tp_size, pp_size):
    """Common assertions for executor initialization tests."""
    world_size = tp_size * pp_size
    expected_output_rank = (pp_size - 1) * tp_size

    assert executor.world_size == world_size
    assert len(executor.ray_worker_handles) == world_size
    assert len(executor.response_mqs) == world_size
    assert executor._get_output_rank() == expected_output_rank

    if pp_size > 1:
        assert executor.max_concurrent_batches == pp_size

    executor.check_health()
    assert not executor.is_failed

    ranks = sorted(h.rank for h in executor.ray_worker_handles)
    assert ranks == list(range(world_size))

    for handle in executor.ray_worker_handles:
        assert handle.node_id is not None