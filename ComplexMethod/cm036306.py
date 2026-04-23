def test_multiprocess_race_construct_and_write(iid):
    """N processes race to construct the same SharedOffloadRegion, each writes
    fill_value = rank+1 into their slot; parent verifies interleaved layout."""
    num_workers = 4
    num_blocks = 3
    total_bytes = num_blocks * num_workers * PAGE_SIZE

    ctx = get_mp_context()
    done_queue = ctx.Queue()
    cleanup_queue = ctx.Queue()

    procs = [
        ctx.Process(
            target=_mp_race_construct_and_write,
            args=(
                iid,
                total_bytes,
                num_blocks,
                rank,
                num_workers,
                PAGE_SIZE,
                rank + 1,
                done_queue,
                cleanup_queue,
            ),
        )
        for rank in range(num_workers)
    ]
    for p in procs:
        p.start()

    results = {}
    for _ in range(num_workers):
        r = done_queue.get(timeout=30)
        results[r["rank"]] = r

    for rank, r in results.items():
        assert r["error"] is None, f"rank {rank}: {r['error']}"

    # Read the raw file while all workers still hold it open.
    mmap_path = f"/dev/shm/vllm_offload_{iid}.mmap"
    with open(mmap_path, "rb") as f:
        raw = f.read()

    for blk in range(num_blocks):
        for w in range(num_workers):
            slot_start = (blk * num_workers + w) * PAGE_SIZE
            slot = raw[slot_start : slot_start + PAGE_SIZE]
            expected = w + 1  # fill_value = rank + 1
            assert all(b == expected for b in slot), (
                f"block {blk}, worker {w}: expected {expected} but got wrong bytes"
            )

    # Unblock all workers to clean up.
    for _ in range(num_workers):
        cleanup_queue.put(True)
    for p in procs:
        p.join(timeout=10)
        assert p.exitcode == 0