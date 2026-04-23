def execute_safe_code(
    code: str,
    extra_globals: Optional[Dict[str, Any]] = None,
    allowed_modules: FrozenSet[str] = SAFE_MODULES,
    timeout: Optional[float] = MAX_EXEC_TIMEOUT,
    max_depth: int = MAX_RECURSION_DEPTH,
) -> SafeExecutionResult:
    """Execute *code* inside a safe sandbox with whitelisted module imports.

    The execution runs in a dedicated thread so that a wall-clock *timeout*
    can be enforced without blocking the caller's event loop.  A custom
    ``sys.setrecursionlimit`` guards against stack-overflow attacks.  Both
    stdout and stderr are capped at :data:`MAX_OUTPUT_BYTES`.

    Args:
        code: Python source code to execute.
        extra_globals: Additional names injected into the execution globals.
        allowed_modules: Frozenset of top-level module names that may be imported.
        timeout: Wall-clock seconds before the execution is abandoned.  Pass
            ``None`` to disable.  Defaults to :data:`MAX_EXEC_TIMEOUT`.
        max_depth: Maximum recursion depth inside the sandbox.  Defaults to
            :data:`MAX_RECURSION_DEPTH`.

    Returns:
        :class:`SafeExecutionResult` containing captured stdout/stderr, any
        ``result`` variable assigned in the code, or error information.
    """
    stdout_buf = _LimitedStringIO(MAX_OUTPUT_BYTES)
    stderr_buf = _LimitedStringIO(MAX_OUTPUT_BYTES)

    safe_globals = _make_safe_globals(allowed_modules, stdout_buf=stdout_buf, stderr_buf=stderr_buf)
    if extra_globals:
        safe_globals.update(extra_globals)

    # Compile outside the thread so SyntaxErrors surface immediately.
    try:
        compiled = compile(code, "<pa_provider>", "exec")
    except SyntaxError:
        return SafeExecutionResult(
            success=False,
            stdout="",
            stderr="",
            error=traceback.format_exc(),
        )

    # Run in a daemon thread with timeout and recursion-depth enforcement.
    # We use a raw daemon Thread (not ThreadPoolExecutor) so that if the
    # sandboxed code runs forever the thread is discarded when the process
    # exits rather than blocking interpreter shutdown.
    exc_box: List = []
    thread = threading.Thread(
        target=_exec_in_thread,
        args=(compiled, safe_globals, safe_globals, max_depth, exc_box),
        daemon=True,
        name="g4f-sandbox",
    )
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # The thread is still running — timeout was hit.  We cannot kill it
        # but as a daemon thread it will be reaped when the process exits.
        stdout = stdout_buf.getvalue()
        stderr = stderr_buf.getvalue()
        if stdout_buf.truncated or stderr_buf.truncated:
            stderr += "\n[Output truncated: size limit reached]"
        return SafeExecutionResult(
            success=False,
            stdout=stdout,
            stderr=stderr,
            error=(
                f"Execution timed out after {timeout:.1f} s. "
                "The thread has been abandoned."
            ),
        )

    if exc_box:
        return SafeExecutionResult(
            success=False,
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue(),
            error=exc_box[0],
        )

    stdout = stdout_buf.getvalue()
    stderr = stderr_buf.getvalue()
    if stdout_buf.truncated or stderr_buf.truncated:
        stderr += "\n[Output truncated: size limit reached]"

    return SafeExecutionResult(
        success=True,
        stdout=stdout,
        stderr=stderr,
        result=safe_globals.get("result"),
        locals=safe_globals,
    )