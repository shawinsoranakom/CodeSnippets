def _resolve_runner_config(
    request: pytest.FixtureRequest,
) -> tuple[str | None, float | None, Path | None]:
    """Return ``(env_file, timeout, base_dir)`` with marker > CLI > env-var precedence."""
    # env_file: marker > --lfx-env-file > LFX_ENV_FILE
    env_file: str | None = (
        _get_marker_arg(request, "lfx_env_file")
        or request.config.getoption("lfx_env_file", default=None)
        or os.environ.get("LFX_ENV_FILE")
    )

    # timeout: marker > --lfx-timeout > LFX_TIMEOUT
    timeout: float | None = _get_marker_arg(request, "lfx_timeout")
    if timeout is None:
        raw_t = request.config.getoption("lfx_timeout", default=None) or os.environ.get("LFX_TIMEOUT")
        if raw_t is not None:
            with contextlib.suppress(TypeError, ValueError):
                timeout = float(raw_t)

    # base_dir: --lfx-flow-dir > LFX_FLOW_DIR > None (defaults to cwd in runner)
    dir_str: str | None = request.config.getoption("lfx_flow_dir", default=None) or os.environ.get("LFX_FLOW_DIR")
    base_dir: Path | None = Path(dir_str) if dir_str else None

    return env_file, timeout, base_dir