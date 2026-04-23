def _install_package_wheel_first(
    *,
    event_queue: Any,
    import_name: str,
    display_name: str,
    pypi_name: str,
    pypi_version: str | None = None,
    filename_prefix: str | None = None,
    release_tag: str | None = None,
    release_base_url: str | None = None,
    wheel_url_builder: Callable[[dict[str, str] | None], str | None] | None = None,
    pypi_spec: str | None = None,
    pypi_status_message: str | None = None,
) -> bool:
    try:
        __import__(import_name)
        logger.info("%s already installed", display_name)
        return True
    except ImportError:
        pass

    env = probe_torch_wheel_env(timeout = 30)
    if wheel_url_builder is not None:
        wheel_url = wheel_url_builder(env)
    else:
        wheel_url = direct_wheel_url(
            filename_prefix = filename_prefix,
            package_version = pypi_version,
            release_tag = release_tag,
            release_base_url = release_base_url,
            env = env,
        )

    if wheel_url is None:
        logger.info("No compatible %s wheel candidate", display_name)
    elif url_exists(wheel_url):
        _send_status(event_queue, f"Installing prebuilt {display_name} wheel...")
        for installer, result in install_wheel(
            wheel_url,
            python_executable = sys.executable,
            use_uv = bool(shutil.which("uv")),
            run = _sp.run,
        ):
            if result.returncode == 0:
                logger.info("Installed prebuilt %s wheel successfully", display_name)
                return True
            logger.warning(
                "%s failed to install %s wheel:\n%s",
                installer,
                display_name,
                result.stdout,
            )
    else:
        logger.info("No published %s wheel found: %s", display_name, wheel_url)

    is_hip = env and env.get("hip_version")
    if is_hip and not shutil.which("hipcc"):
        logger.error(
            "%s requires hipcc for source compilation on ROCm. "
            "Install the ROCm HIP SDK: https://rocm.docs.amd.com",
            display_name,
        )
        _send_status(
            event_queue,
            f"{display_name}: hipcc not found (ROCm HIP SDK required)",
        )
        return False

    if pypi_spec is None:
        pypi_spec = f"{pypi_name}=={pypi_version}"

    if pypi_status_message is None:
        if is_hip:
            pypi_status_message = (
                f"Compiling {display_name} from source for ROCm "
                "(this may take several minutes)..."
            )
        else:
            pypi_status_message = f"Installing {display_name} from PyPI..."

    _send_status(event_queue, pypi_status_message)

    # Prefer uv for faster dependency resolution when available
    plain_pypi_install = pypi_version is None
    if plain_pypi_install:
        if shutil.which("uv"):
            pypi_cmd = [
                "uv",
                "pip",
                "install",
                "--python",
                sys.executable,
                pypi_spec,
            ]
        else:
            pypi_cmd = [sys.executable, "-m", "pip", "install", pypi_spec]
    else:
        if shutil.which("uv"):
            pypi_cmd = [
                "uv",
                "pip",
                "install",
                "--python",
                sys.executable,
                "--no-build-isolation",
                "--no-deps",
            ]
            # Avoid stale cache artifacts from partial HIP source builds
            if is_hip:
                pypi_cmd.append("--no-cache")
            pypi_cmd.append(pypi_spec)
        else:
            pypi_cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-build-isolation",
                "--no-deps",
                "--no-cache-dir",
                pypi_spec,
            ]

    # Source compilation on ROCm can take 10-30 minutes; use a generous
    # timeout. Non-HIP installs preserve the pre-existing "no timeout"
    # behaviour so unrelated slow installs (e.g. causal-conv1d source
    # build on Linux aarch64 or unsupported torch/CUDA combinations)
    # are not aborted at 5 minutes by this PR.
    _run_kwargs: dict[str, Any] = {
        "stdout": _sp.PIPE,
        "stderr": _sp.STDOUT,
        "text": True,
    }
    if is_hip:
        _run_kwargs["timeout"] = 1800

    try:
        result = _sp.run(pypi_cmd, **_run_kwargs)
    except _sp.TimeoutExpired:
        logger.error(
            "%s installation timed out after %ds",
            display_name,
            _run_kwargs.get("timeout"),
        )
        _send_status(
            event_queue,
            f"{display_name} installation timed out after "
            f"{_run_kwargs.get('timeout')}s",
        )
        return False

    if result.returncode != 0:
        if is_hip:
            # Surface a clear error for ROCm source build failures
            error_lines = (result.stdout or "").strip().splitlines()
            snippet = "\n".join(error_lines[-5:]) if error_lines else "(no output)"
            logger.error(
                "Failed to compile %s for ROCm:\n%s",
                display_name,
                result.stdout,
            )
            _send_status(
                event_queue,
                f"Failed to compile {display_name} for ROCm. "
                "Check that hipcc and ROCm development headers are installed.\n"
                f"{snippet}",
            )
        else:
            logger.error(
                "Failed to install %s from PyPI:\n%s",
                display_name,
                result.stdout,
            )
        return False

    if is_hip:
        logger.info("Compiled and installed %s from source for ROCm", display_name)
    else:
        logger.info("Installed %s from PyPI", display_name)
    return True