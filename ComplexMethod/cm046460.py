def _detect_host_rocm_version() -> tuple[int, int] | None:
    """Return (major, minor) of the installed ROCm runtime, or None.

    Best-effort read from /opt/rocm/.info/version, amd-smi version, and
    hipconfig --version. Used to pick a compatible upstream llama.cpp
    ROCm prebuilt rather than always taking the numerically newest one
    (which can be newer than the host runtime).
    """
    rocm_root = os.environ.get("ROCM_PATH") or "/opt/rocm"
    for path in (
        os.path.join(rocm_root, ".info", "version"),
        os.path.join(rocm_root, "lib", "rocm_version"),
    ):
        try:
            with open(path) as fh:
                parts = fh.read().strip().split("-")[0].split(".")
            # Explicit length guard avoids relying on the broad except
            # below to swallow IndexError when the version file contains
            # a single component (e.g. "6\n" on a partial install).
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
        except Exception:
            pass
    amd_smi = shutil.which("amd-smi")
    if amd_smi:
        try:
            result = subprocess.run(
                [amd_smi, "version"],
                stdout = subprocess.PIPE,
                stderr = subprocess.DEVNULL,
                text = True,
                timeout = 5,
            )
            if result.returncode == 0:
                m = re.search(r"ROCm version:\s*(\d+)\.(\d+)", result.stdout)
                if m:
                    return int(m.group(1)), int(m.group(2))
        except Exception:
            pass
    hipconfig = shutil.which("hipconfig")
    if hipconfig:
        try:
            result = subprocess.run(
                [hipconfig, "--version"],
                stdout = subprocess.PIPE,
                stderr = subprocess.DEVNULL,
                text = True,
                timeout = 5,
            )
            if result.returncode == 0:
                raw = (result.stdout or "").strip().split("\n")[0]
                parts = raw.split(".")
                if (
                    len(parts) >= 2
                    and parts[0].isdigit()
                    and parts[1].split("-")[0].isdigit()
                ):
                    return int(parts[0]), int(parts[1].split("-")[0])
        except Exception:
            pass

    # Distro package-manager fallbacks. Mirrors install.sh::get_torch_index_url
    # and _detect_rocm_version() in install_python_stack.py so package-managed
    # ROCm hosts without /opt/rocm/.info/version still report a usable version
    # and the <= host version filter in resolve_upstream_asset_choice picks
    # the correct upstream prebuilt instead of the newest-regardless fallback.
    for _cmd in (
        ["dpkg-query", "-W", "-f=${Version}\n", "rocm-core"],
        ["rpm", "-q", "--qf", "%{VERSION}\n", "rocm-core"],
    ):
        _exe = shutil.which(_cmd[0])
        if not _exe:
            continue
        try:
            _result = subprocess.run(
                [_exe, *_cmd[1:]],
                stdout = subprocess.PIPE,
                stderr = subprocess.DEVNULL,
                text = True,
                timeout = 5,
            )
        except Exception:
            continue
        if _result.returncode != 0 or not _result.stdout.strip():
            continue
        _raw = _result.stdout.strip()
        # dpkg can prepend an epoch ("1:6.3.0-1"); strip it before parsing.
        _raw = re.sub(r"^\d+:", "", _raw)
        _m = re.match(r"(\d+)[.-](\d+)", _raw)
        if _m:
            return int(_m.group(1)), int(_m.group(2))
    return None