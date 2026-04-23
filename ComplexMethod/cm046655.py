def _bash_exec(
    command: str,
    cancel_event = None,
    timeout: int = _EXEC_TIMEOUT,
    session_id: str | None = None,
) -> str:
    """Execute a bash command in a subprocess sandbox."""
    if not command or not command.strip():
        return "No command provided."

    # Block dangerous commands (shlex + regex based)
    blocked = _find_blocked_commands(command)
    if blocked:
        return f"Blocked command(s) for safety: {', '.join(sorted(blocked))}"

    try:
        workdir = _get_workdir(session_id)
        safe_env = _build_safe_env(workdir)
        popen_kwargs = dict(
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True,
            cwd = workdir,
            env = safe_env,
        )
        if sys.platform != "win32":
            popen_kwargs["preexec_fn"] = _sandbox_preexec
        else:
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(_get_shell_cmd(command), **popen_kwargs)

        if cancel_event is not None:
            watcher = threading.Thread(
                target = _cancel_watcher, args = (proc, cancel_event), daemon = True
            )
            watcher.start()

        try:
            output, _ = proc.communicate(timeout = timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return _truncate(f"Execution timed out after {timeout} seconds.")

        if cancel_event is not None and cancel_event.is_set():
            return "Execution cancelled."

        result = output or ""
        if proc.returncode != 0:
            result = f"Exit code {proc.returncode}:\n{result}"
        return _truncate(result) if result.strip() else "(no output)"

    except Exception as e:
        return f"Execution error: {e}"