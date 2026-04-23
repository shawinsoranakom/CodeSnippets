async def _assert_children_cleaned_up(
    child_pids: list[int],
    timeout: float = _CHILD_CLEANUP_TIMEOUT,
):
    """Wait for child processes to exit and fail if any remain."""
    if not child_pids:
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        still_alive = []
        for pid in child_pids:
            try:
                p = psutil.Process(pid)
                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                    still_alive.append(pid)
            except psutil.NoSuchProcess:
                pass
        if not still_alive:
            return
        await asyncio.sleep(0.5)

    pytest.fail(
        f"Child processes {still_alive} still alive after {timeout}s. "
        f"Process cleanup may not be working correctly."
    )