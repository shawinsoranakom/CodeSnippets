async def run_sandboxed(
    command: list[str],
    cwd: str,
    timeout: int = _DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> tuple[str, str, int, bool]:
    """Run a command inside a bubblewrap sandbox.

    Callers **must** check :func:`has_full_sandbox` before calling this
    function.  If bubblewrap is not available, this function raises
    :class:`RuntimeError` rather than running unsandboxed.

    Returns:
        (stdout, stderr, exit_code, timed_out)
    """
    if not has_full_sandbox():
        raise RuntimeError(
            "run_sandboxed() requires bubblewrap but bwrap is not available. "
            "Callers must check has_full_sandbox() before calling this function."
        )

    timeout = min(max(timeout, 1), _MAX_TIMEOUT)

    safe_env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": cwd,
        "TMPDIR": cwd,
        "LANG": "en_US.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    if env:
        safe_env.update(env)

    full_command = _build_bwrap_command(command, cwd, safe_env)

    try:
        proc = await asyncio.create_subprocess_exec(
            *full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=safe_env,
            start_new_session=True,  # Own process group for clean kill
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            return stdout, stderr, proc.returncode or 0, False
        except asyncio.TimeoutError:
            # Kill entire process group (bwrap + all children).
            # proc.kill() alone only kills the bwrap parent, leaving
            # children running until they finish naturally.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Already exited
            except OSError as kill_err:
                logger.warning(
                    "Failed to kill process group %d: %s", proc.pid, kill_err
                )
            # Always reap the subprocess regardless of killpg outcome.
            await proc.communicate()
            return "", f"Execution timed out after {timeout}s", -1, True

    except RuntimeError:
        raise
    except Exception as e:
        return "", f"Sandbox error: {e}", -1, False