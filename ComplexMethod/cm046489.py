def pip_install_try(
    label: str,
    *args: str,
    constrain: bool = True,
) -> bool:
    """Like pip_install but returns False on failure instead of exiting.
    For optional installs with a follow-up fallback.
    """
    constraint_args: list[str] = []
    if constrain and CONSTRAINTS.is_file():
        constraint_args = ["-c", str(CONSTRAINTS)]

    if USE_UV:
        cmd = _build_uv_cmd(args) + constraint_args
    else:
        cmd = _build_pip_cmd(args) + constraint_args

    if VERBOSE:
        _step(_LABEL, f"{label}...", _dim)
    result = subprocess.run(
        cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
    )
    if result.returncode == 0:
        return True
    if VERBOSE and result.stdout:
        print(result.stdout.decode(errors = "replace"))
    return False