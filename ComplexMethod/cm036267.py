def _assert_right_encoder_cache_allocated(
    scheduler: Scheduler,
    hashes_to_check: list[str] | None = None,
    requests: list[Request] | None = None,
    expected_total_allocated: int | None = None,
):
    """Check whether encoder cache is allocated correctly."""
    encoder_cache_manager = scheduler.encoder_cache_manager

    # Verify encoder cache manager exists
    assert encoder_cache_manager is not None, "Encoder cache manager should exist"

    # Verify number of cache
    if expected_total_allocated is not None:
        assert len(encoder_cache_manager.cached) == expected_total_allocated
        if expected_total_allocated == 0:
            return

    # Verify each request with MM data is in cache
    cached_hashes = set(encoder_cache_manager.cached.keys())

    if hashes_to_check:
        missed_hashes = set(hashes_to_check) - cached_hashes
        assert not missed_hashes, (
            f"Miss hashes: {missed_hashes} "
            f"Existing encoder cache: {encoder_cache_manager.cached}"
        )

    for req in requests if requests is not None else []:
        if req.mm_features:
            mm_hashes = [f.identifier for f in req.mm_features]
            req_hashes = set(mm_hashes)  # unique hashes set
            missed_hashes = req_hashes - cached_hashes
            assert not missed_hashes, (
                f"Miss hashes in cache for request {req.request_id}: {missed_hashes} "
                f"Existing encoder cache: {encoder_cache_manager.cached}"
            )