def install_python_stack() -> int:
    global USE_UV, _STEP, _TOTAL
    _STEP = 0

    # When called from install.sh (which already installed unsloth into the venv),
    # SKIP_STUDIO_BASE=1 is set to avoid redundant reinstallation of base packages.
    # When called from "unsloth studio update", it is NOT set so base packages
    # (unsloth + unsloth-zoo) are always reinstalled to pick up new versions.
    skip_base = os.environ.get("SKIP_STUDIO_BASE", "0") == "1"
    # When --package is used, install a different package name (e.g. roland-sloth for testing)
    package_name = os.environ.get("STUDIO_PACKAGE_NAME", "unsloth")
    # When --local is used, overlay a local repo checkout after updating deps
    local_repo = os.environ.get("STUDIO_LOCAL_REPO", "")
    base_total = 10 if IS_WINDOWS else 11
    if IS_MACOS:
        base_total -= 1  # triton step is skipped on macOS
    if not IS_WINDOWS and not IS_MACOS and not NO_TORCH:
        base_total += 3
    _TOTAL = (base_total - 1) if skip_base else base_total

    # 1. Try to use uv for faster installs (must happen before pip upgrade
    #    because uv venvs don't include pip by default)
    USE_UV = _bootstrap_uv()

    # 2. Ensure pip is available (uv venvs created by install.sh don't include pip)
    _progress("pip bootstrap")
    if USE_UV:
        run(
            "Bootstrapping pip via uv",
            [
                "uv",
                "pip",
                "install",
                "--python",
                sys.executable,
                "pip",
            ],
        )
    else:
        # pip may not exist yet (uv-created venvs omit it). Try ensurepip
        # first, then upgrade. Only fall back to a direct upgrade when pip
        # is already present.
        _has_pip = (
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                stdout = subprocess.DEVNULL,
                stderr = subprocess.DEVNULL,
            ).returncode
            == 0
        )

        if not _has_pip:
            run(
                "Bootstrapping pip via ensurepip",
                [sys.executable, "-m", "ensurepip", "--upgrade"],
            )
        else:
            run(
                "Upgrading pip",
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            )

    # 3. Core packages: unsloth-zoo + unsloth (or custom package name)
    if skip_base:
        pass
    elif NO_TORCH:
        # No-torch update path: install unsloth + unsloth-zoo with --no-deps
        # (current PyPI metadata still declares torch as a hard dep), then
        # runtime deps with --no-deps (avoids transitive torch).
        _progress("base packages (no torch)")
        pip_install(
            f"Updating {package_name} + unsloth-zoo (no-torch mode)",
            "--no-cache-dir",
            "--no-deps",
            "--upgrade-package",
            package_name,
            "--upgrade-package",
            "unsloth-zoo",
            package_name,
            "unsloth-zoo",
        )
        pip_install(
            "Installing no-torch runtime deps",
            "--no-cache-dir",
            "--no-deps",
            req = REQ_ROOT / "no-torch-runtime.txt",
        )
        if local_repo:
            pip_install(
                "Overlaying local repo (editable)",
                "--no-cache-dir",
                "--no-deps",
                "-e",
                local_repo,
                constrain = False,
            )
    elif local_repo:
        # Local dev install: update deps from base.txt, then overlay the
        # local checkout as an editable install (--no-deps so torch is
        # never re-resolved).
        _progress("base packages")
        pip_install(
            "Updating base packages",
            "--no-cache-dir",
            "--upgrade-package",
            "unsloth",
            "--upgrade-package",
            "unsloth-zoo",
            req = REQ_ROOT / "base.txt",
        )
        pip_install(
            "Overlaying local repo (editable)",
            "--no-cache-dir",
            "--no-deps",
            "-e",
            local_repo,
            constrain = False,
        )
    elif package_name != "unsloth":
        # Custom package name (e.g. roland-sloth for testing) — install directly
        _progress("base packages")
        pip_install(
            f"Installing {package_name}",
            "--no-cache-dir",
            package_name,
        )
    else:
        # Update path: upgrade only unsloth + unsloth-zoo while preserving
        # existing torch/CUDA installations.  Torch is pre-installed by
        # install.sh / setup.ps1; --upgrade-package targets only base pkgs.
        _progress("base packages")
        pip_install(
            "Updating base packages",
            "--no-cache-dir",
            "--upgrade-package",
            "unsloth",
            "--upgrade-package",
            "unsloth-zoo",
            req = REQ_ROOT / "base.txt",
        )

    # 2b. AMD ROCm: reinstall torch with HIP wheels if the host has ROCm but the
    #     venv received CPU-only torch (common when pip resolves torch from PyPI).
    #     Must come immediately after base packages so torch is present for inspection.
    if not IS_WINDOWS and not IS_MACOS and not NO_TORCH:
        _progress("ROCm torch check")
        _ensure_rocm_torch()

    # Windows + AMD GPU: PyTorch does not publish ROCm wheels for Windows.
    # Detect and warn so users know manual steps are needed for GPU training.
    if IS_WINDOWS and not NO_TORCH and not _has_usable_nvidia_gpu():
        # Validate actual AMD GPU presence (not just tool existence)
        import re as _re_win

        def _win_amd_smi_has_gpu(stdout: str) -> bool:
            return bool(_re_win.search(r"(?im)^gpu\s*[:\[]\s*\d", stdout))

        _win_amd_gpu = False
        for _wcmd, _check_fn in (
            (["hipinfo"], lambda out: "gcnarchname" in out.lower()),
            (["amd-smi", "list"], _win_amd_smi_has_gpu),
        ):
            _wexe = shutil.which(_wcmd[0])
            if not _wexe:
                continue
            try:
                _wr = subprocess.run(
                    [_wexe, *_wcmd[1:]],
                    stdout = subprocess.PIPE,
                    stderr = subprocess.DEVNULL,
                    text = True,
                    timeout = 10,
                )
            except Exception:
                continue
            if _wr.returncode == 0 and _check_fn(_wr.stdout):
                _win_amd_gpu = True
                break
        if _win_amd_gpu:
            _safe_print(
                _dim("  Note:"),
                "AMD GPU detected on Windows. ROCm-enabled PyTorch must be",
            )
            _safe_print(
                " " * 8,
                "installed manually. See: https://docs.unsloth.ai/get-started/install-and-update/amd",
            )

    # 3. Extra dependencies
    _progress("unsloth extras")
    pip_install(
        "Installing additional unsloth dependencies",
        "--no-cache-dir",
        req = REQ_ROOT / "extras.txt",
    )

    # 3b. Extra dependencies (no-deps) -- audio model support etc.
    _progress("extra codecs")
    pip_install(
        "Installing extras (no-deps)",
        "--no-deps",
        "--no-cache-dir",
        req = REQ_ROOT / "extras-no-deps.txt",
    )

    # 4. Overrides (torchao, transformers) -- force-reinstall
    #    Skip entirely when torch is unavailable (e.g. Intel Mac GGUF-only mode)
    #    because overrides.txt contains torchao which requires torch.
    if NO_TORCH:
        _progress("dependency overrides (skipped, no torch)")
    else:
        _progress("dependency overrides")
        pip_install(
            "Installing dependency overrides",
            "--force-reinstall",
            "--no-cache-dir",
            req = REQ_ROOT / "overrides.txt",
        )

    # 5. Triton kernels (no-deps, from source)
    #    Skip on Windows (no support) and macOS (no support).
    if not IS_WINDOWS and not IS_MACOS:
        _progress("triton kernels")
        pip_install(
            "Installing triton kernels",
            "--no-deps",
            "--no-cache-dir",
            req = REQ_ROOT / "triton-kernels.txt",
            constrain = False,
        )

    if not IS_WINDOWS and not IS_MACOS and not NO_TORCH:
        _progress("flash-attn")
        _ensure_flash_attn()

    # # 6. Patch: override llama_cpp.py with fix from unsloth-zoo  feature/llama-cpp-windows-support branch
    # patch_package_file(
    #     "unsloth-zoo",
    #     os.path.join("unsloth_zoo", "llama_cpp.py"),
    #     "https://raw.githubusercontent.com/unslothai/unsloth-zoo/refs/heads/main/unsloth_zoo/llama_cpp.py",
    # )

    # # 7a. Patch: override vision.py with fix from unsloth PR #4091
    # patch_package_file(
    #     "unsloth",
    #     os.path.join("unsloth", "models", "vision.py"),
    #     "https://raw.githubusercontent.com/unslothai/unsloth/80e0108a684c882965a02a8ed851e3473c1145ab/unsloth/models/vision.py",
    # )

    # # 7b. Patch : override save.py with fix from feature/llama-cpp-windows-support
    # patch_package_file(
    #     "unsloth",
    #     os.path.join("unsloth", "save.py"),
    #     "https://raw.githubusercontent.com/unslothai/unsloth/refs/heads/main/unsloth/save.py",
    # )

    # 8. Studio dependencies
    _progress("studio deps")
    pip_install(
        "Installing studio dependencies",
        "--no-cache-dir",
        req = REQ_ROOT / "studio.txt",
    )

    # 9. Data-designer dependencies
    _progress("data designer deps")
    pip_install(
        "Installing data-designer base dependencies",
        "--no-cache-dir",
        req = SINGLE_ENV / "data-designer-deps.txt",
    )

    # 10. Data-designer packages (no-deps to avoid conflicts)
    _progress("data designer")
    pip_install(
        "Installing data-designer",
        "--no-cache-dir",
        "--no-deps",
        req = SINGLE_ENV / "data-designer.txt",
    )

    # 11. Local Data Designer seed plugin
    if not LOCAL_DD_UNSTRUCTURED_PLUGIN.is_dir():
        _safe_print(
            _red(
                f"❌ Missing local plugin directory: {LOCAL_DD_UNSTRUCTURED_PLUGIN}",
            ),
        )
        return 1
    _progress("local plugin")
    pip_install(
        "Installing local data-designer unstructured plugin",
        "--no-cache-dir",
        "--no-deps",
        str(LOCAL_DD_UNSTRUCTURED_PLUGIN),
        constrain = False,
    )

    # 12. Patch metadata for single-env compatibility
    _progress("finalizing")
    run(
        "Patching single-env metadata",
        [sys.executable, str(SINGLE_ENV / "patch_metadata.py")],
    )

    # 13. AMD ROCm: final torch repair.  Multiple install steps above can
    #     pull in CUDA torch from PyPI (base packages, extras, overrides,
    #     studio deps, etc.).  Running the repair as the very last step
    #     ensures ROCm torch is in place at runtime, regardless of which
    #     intermediate step clobbered it.
    if not IS_WINDOWS and not IS_MACOS and not NO_TORCH:
        _progress("ROCm torch (final)")
        _ensure_rocm_torch()

    # 14. Final check (silent; third-party conflicts are expected)
    subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        stdout = subprocess.DEVNULL,
        stderr = subprocess.DEVNULL,
    )

    _step(_LABEL, "installed")
    return 0