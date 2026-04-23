def _terminate_executor_processes(executor):
    """强制终止 ProcessPoolExecutor 中的所有子进程"""
    processes = list(getattr(executor, "_processes", {}).values())
    if not processes:
        return

    alive_processes = []
    for process in processes:
        if not process.is_alive():
            continue
        try:
            process.terminate()
        except Exception:
            pass
        alive_processes.append(process)

    deadline = time.monotonic() + PDF_RENDER_TERMINATE_GRACE_PERIOD_SECONDS
    for process in alive_processes:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            process.join(timeout=remaining)
        except Exception:
            pass

    for process in alive_processes:
        if not process.is_alive():
            continue
        try:
            kill_process = getattr(process, "kill", None)
            if callable(kill_process):
                kill_process()
            else:
                process.terminate()
        except Exception:
            pass

    for process in alive_processes:
        if not process.is_alive():
            continue
        try:
            process.join(timeout=PDF_RENDER_KILL_JOIN_TIMEOUT_SECONDS)
        except Exception:
            pass