def _wait_and_terminate(
    checker: FileLinesNumberChecker,
    timeout_sec: float,
    proc: subprocess.Popen,
    *,
    double_check_interval: float | None = None,
    persistence_flush_sec: float = 5.0,
) -> None:
    """Poll checker until it passes, sleep for persistence flush, then kill proc."""
    start = time.monotonic()
    while True:
        time.sleep(0.1)
        elapsed = time.monotonic() - start
        if elapsed >= timeout_sec:
            proc.terminate()
            proc.wait()
            raise AssertionError(
                f"Timed out after {timeout_sec}s. "
                f"{checker.provide_information_on_failure()}"
            )
        if checker():
            if double_check_interval is not None:
                time.sleep(double_check_interval)
                if not checker():
                    proc.terminate()
                    proc.wait()
                    raise AssertionError(
                        f"Double-check failed. "
                        f"{checker.provide_information_on_failure()}"
                    )
            break
        if proc.poll() is not None:
            assert (
                proc.returncode == 0
            ), f"Subprocess exited with code {proc.returncode}"
            break
    time.sleep(persistence_flush_sec)
    proc.terminate()
    proc.wait()