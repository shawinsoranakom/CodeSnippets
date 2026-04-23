def process_tracker():
    """Track subprocess count for memory leak detection."""
    process = psutil.Process()
    initial_count = len(process.children(recursive=True))

    yield process, initial_count

    # Give some time for cleanup to complete before checking for leftover processes
    # Collect child processes that we expect to wait for
    try:
        children = process.children(recursive=True)
        if not children:
            return

        gone, alive = psutil.wait_procs(children, timeout=2)
        if gone:
            logger.debug("Processes exited naturally: %s", [p.pid for p in gone])

        if alive:
            logger.debug("Processes still alive after 2s: %s", [p.pid for p in alive])
            for p in alive:
                with contextlib.suppress(psutil.NoSuchProcess):
                    p.terminate()

            gone2, alive2 = psutil.wait_procs(alive, timeout=5)
            if gone2:
                logger.debug("Processes terminated gracefully: %s", [p.pid for p in gone2])

            for p in alive2:
                with contextlib.suppress(psutil.NoSuchProcess):
                    p.kill()

            _ = psutil.wait_procs(alive2, timeout=2)

        leftover = process.children(recursive=True)
        assert not leftover, f"Leftover child processes: {[p.pid for p in leftover]}"

    except Exception as e:
        logger.exception("Error cleaning up child processes: %s", e)