def distributed_run(fn, world_size, timeout=60):
    """Run a function in multiple processes with proper error handling.

    Args:
        fn: Function to run in each process
        world_size: Number of processes to spawn
        timeout: Maximum time in seconds to wait for processes (default: 60)
    """
    number_of_processes = world_size
    processes = []
    for i in range(number_of_processes):
        env = {}
        env["RANK"] = str(i)
        env["LOCAL_RANK"] = str(i)
        env["WORLD_SIZE"] = str(number_of_processes)
        env["LOCAL_WORLD_SIZE"] = str(number_of_processes)
        env["MASTER_ADDR"] = "localhost"
        env["MASTER_PORT"] = "12345"
        p = mp.Process(target=fn, args=(env,))
        processes.append(p)
        p.start()

    # Monitor processes and fail fast if any process fails
    start_time = time.time()
    failed_processes = []

    # Wait for all processes, checking for failures
    while time.time() - start_time < timeout:
        all_done = True
        for i, p in enumerate(processes):
            if p.is_alive():
                all_done = False
            elif p.exitcode != 0:
                # Process failed
                failed_processes.append((i, p.exitcode))
                break

        if failed_processes or all_done:
            break
        time.sleep(0.1)  # Check every 100ms

    # Check for timeout if no failures detected yet
    for i, p in enumerate(processes):
        if p.is_alive():
            p.kill()
            p.join()

    # Report failures
    if failed_processes:
        error_msg = "Distributed test failed:\n"
        for rank, status in failed_processes:
            error_msg += f"  Rank {rank}: Exit code {status}\n"
        raise AssertionError(error_msg)