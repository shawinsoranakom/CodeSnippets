def test_multi_worker_race_exactly_one_creator(iid):
    """When N threads race to create the same region, exactly one becomes creator."""
    num_workers = 8
    regions, errors = _race_construct(iid, num_workers=num_workers)
    try:
        assert not errors, f"Workers raised: {errors}"
        assert len(regions) == num_workers, "Some workers failed to construct"

        creators = [r for r in regions if r._creator]
        assert len(creators) == 1, f"Expected 1 creator, got {len(creators)}"
        assert sum(1 for r in regions if not r._creator) == num_workers - 1, (
            f"Expected {num_workers - 1} non-creators, got "
            f"{sum(1 for r in regions if not r._creator)}"
        )

        for r in regions:
            assert not r.mmap_obj.closed
            assert r.total_size_bytes == 4 * num_workers * PAGE_SIZE
    finally:
        for r in regions:
            r.cleanup()
        _cleanup_file(regions[0].mmap_path)