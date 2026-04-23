def distributed_run(fn, world_size, *args):
    number_of_processes = world_size
    processes: list[mp.Process] = []
    skip_queue: mp.SimpleQueue = mp.SimpleQueue()
    for i in range(number_of_processes):
        env: dict[str, str] = {}
        env["RANK"] = str(i)
        env["LOCAL_RANK"] = str(i)
        env["WORLD_SIZE"] = str(number_of_processes)
        env["LOCAL_WORLD_SIZE"] = str(number_of_processes)
        env["MASTER_ADDR"] = "localhost"
        env["MASTER_PORT"] = "12345"
        p = mp.Process(
            target=_distributed_worker_wrapper,
            args=(fn, env, world_size, args, i, skip_queue),
        )
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    skipped: list[tuple[int, str]] = []
    while not skip_queue.empty():
        rank, reason = skip_queue.get()
        skipped.append((rank, reason))

    if len(skipped) == number_of_processes:
        reason = skipped[0][1]
        pytest.skip(reason)
    if 0 < len(skipped) < number_of_processes:
        skipped_ranks = sorted(rank for rank, _ in skipped)
        raise AssertionError(
            "Distributed test had partial skips; expected either all ranks "
            f"to skip or none. Skipped ranks: {skipped_ranks}, "
            f"total ranks: {number_of_processes}"
        )

    for p in processes:
        assert p.exitcode == 0