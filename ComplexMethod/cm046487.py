def _ensure_rocm_torch() -> None:
    """Reinstall torch with ROCm wheels when the venv received CPU-only torch.

    Runs only on Linux x86_64 hosts where an AMD GPU is present and the
    ROCm runtime is detectable (rocminfo / amd-smi / hipconfig /
    rocm-core package).  No-op when torch already links against HIP
    (ROCm), on Windows / macOS, on non-x86_64 Linux (PyTorch does not
    publish ROCm wheels for aarch64 / arm64), or on mixed AMD+NVIDIA
    hosts (NVIDIA takes precedence).
    Uses pip_install() to respect uv, constraints, and --python targeting.
    """
    # Explicit OS / architecture guards so the helper is safe to call
    # from any context -- PyTorch only publishes ROCm wheels for
    # linux_x86_64, so aarch64 / arm64 hosts must skip this repair path
    # instead of failing the update with a missing-wheel error.
    if IS_WINDOWS or IS_MACOS:
        return
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        return
    # NVIDIA takes precedence on mixed hosts -- but only if an actual GPU is usable
    if _has_usable_nvidia_gpu():
        return
    # Rely on _has_rocm_gpu() (rocminfo / amd-smi GPU data rows) as the
    # authoritative "is this actually an AMD ROCm host?" signal. The old
    # gate required /opt/rocm or hipcc to exist, which breaks on
    # runtime-only ROCm installs (package-managed minimal installs,
    # Radeon software) that ship amd-smi/rocminfo without /opt/rocm or
    # hipcc, and leaves `unsloth studio update` unable to repair a
    # CPU-only venv on those systems.
    if not _has_rocm_gpu():
        return  # no AMD GPU visible

    ver = _detect_rocm_version()
    if ver is None:
        print("   ROCm detected but version unreadable -- skipping torch reinstall")
        return

    # Probe whether torch already links against HIP (ROCm is already working).
    # Do NOT skip for CUDA-only builds since they are unusable on AMD-only
    # hosts (the NVIDIA check above already handled mixed AMD+NVIDIA setups).
    try:
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import torch; print(getattr(torch.version,'hip','') or '')",
            ],
            stdout = subprocess.PIPE,
            stderr = subprocess.DEVNULL,
            timeout = 30,
        )
    except (OSError, subprocess.TimeoutExpired):
        probe = None
    has_hip_torch = (
        probe is not None
        and probe.returncode == 0
        and probe.stdout.decode().strip() != ""
    )

    rocm_torch_ready = has_hip_torch

    if not has_hip_torch:
        # Select best matching wheel tag (newest ROCm version <= installed)
        tag = next(
            (
                t
                for (maj, mn), t in sorted(_ROCM_TORCH_INDEX.items(), reverse = True)
                if ver >= (maj, mn)
            ),
            None,
        )
        if tag is None:
            print(
                f"   No PyTorch wheel for ROCm {ver[0]}.{ver[1]} -- "
                f"skipping torch reinstall"
            )
        else:
            index_url = f"{_PYTORCH_WHL_BASE}/{tag}"
            print(f"   ROCm {ver[0]}.{ver[1]} -- installing torch from {index_url}")
            pip_install(
                f"ROCm torch ({tag})",
                "--force-reinstall",
                "--no-cache-dir",
                "torch>=2.4,<2.11.0",
                "torchvision<0.26.0",
                "torchaudio<2.11.0",
                "--index-url",
                index_url,
                constrain = False,
            )
            rocm_torch_ready = True

    # Install bitsandbytes only when torch links against ROCm. Prefers the
    # continuous-release_main wheel (bnb PR #1887 4-bit GEMV fix) and falls
    # back to PyPI when the pre-release URL is unreachable.
    if rocm_torch_ready:
        _bnb_url = _bnb_rocm_prerelease_url()
        _bnb_installed = False
        if _bnb_url is not None:
            _bnb_installed = pip_install_try(
                "bitsandbytes (AMD, pre-release main)",
                "--force-reinstall",
                "--no-cache-dir",
                "--no-deps",
                _bnb_url,
                constrain = False,
            )
            if not _bnb_installed:
                print(
                    _red(
                        "   bnb pre-release unreachable; falling back to PyPI "
                        "(4-bit decode will be broken on ROCm)"
                    )
                )
        if not _bnb_installed:
            pip_install(
                "bitsandbytes (AMD)",
                "--force-reinstall",
                "--no-cache-dir",
                "--no-deps",
                _BNB_ROCM_PYPI_FALLBACK,
                constrain = False,
            )