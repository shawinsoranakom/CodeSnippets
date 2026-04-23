def _ensure_flash_attn() -> None:
    if NO_TORCH or IS_WINDOWS or IS_MACOS:
        return
    if _flash_attn_install_disabled():
        return
    if (
        subprocess.run(
            [sys.executable, "-c", "import flash_attn"],
            stdout = subprocess.DEVNULL,
            stderr = subprocess.DEVNULL,
        ).returncode
        == 0
    ):
        return

    env = probe_torch_wheel_env()
    wheel_url = _build_flash_attn_wheel_url(env) if env else None
    if wheel_url and url_exists(wheel_url):
        for installer, wheel_result in install_wheel(
            wheel_url,
            python_executable = sys.executable,
            use_uv = USE_UV,
            uv_needs_system = UV_NEEDS_SYSTEM,
        ):
            if wheel_result.returncode == 0:
                return
            _print_optional_install_failure(
                f"Installing flash-attn prebuilt wheel with {installer}",
                wheel_result,
            )
        _step("warning", "Continuing without flash-attn", _cyan)
        return

    if wheel_url is None:
        _step("warning", "No compatible flash-attn prebuilt wheel found", _cyan)
    else:
        _step("warning", "No published flash-attn prebuilt wheel found", _cyan)