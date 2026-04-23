def pip_install(
    label: str,
    *args: str,
    req: Path | None = None,
    constrain: bool = True,
) -> None:
    """Build and run a pip install command (uses uv when available, falls back to pip)."""
    constraint_args: list[str] = []
    if constrain and CONSTRAINTS.is_file():
        constraint_args = ["-c", str(CONSTRAINTS)]

    actual_req = req
    temp_reqs: list[Path] = []
    if req is not None and IS_WINDOWS and WINDOWS_SKIP_PACKAGES:
        actual_req = _filter_requirements(req, WINDOWS_SKIP_PACKAGES)
        temp_reqs.append(actual_req)
    if actual_req is not None and NO_TORCH and NO_TORCH_SKIP_PACKAGES:
        actual_req = _filter_requirements(actual_req, NO_TORCH_SKIP_PACKAGES)
        temp_reqs.append(actual_req)
    req_args: list[str] = []
    if actual_req is not None:
        req_args = ["-r", str(actual_req)]

    try:
        if USE_UV:
            uv_cmd = _build_uv_cmd(args) + constraint_args + req_args
            if VERBOSE:
                print(f"   {label}...")
            result = subprocess.run(
                uv_cmd,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
            )
            if result.returncode == 0:
                return
            print(_red(f"   uv failed, falling back to pip..."))
            if result.stdout:
                print(result.stdout.decode(errors = "replace"))

        pip_cmd = _build_pip_cmd(args) + constraint_args + req_args
        run(f"{label} (pip)" if USE_UV else label, pip_cmd)
    finally:
        for temp_req in temp_reqs:
            temp_req.unlink(missing_ok = True)