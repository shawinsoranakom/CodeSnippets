def _detect_rocm_version() -> tuple[int, int] | None:
    """Return (major, minor) of the installed ROCm stack, or None."""
    # Check /opt/rocm/.info/version or ROCM_PATH equivalent
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

    # Try amd-smi version (outputs "... | ROCm version: X.Y.Z")
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
                import re

                m = re.search(r"ROCm version:\s*(\d+)\.(\d+)", result.stdout)
                if m:
                    return int(m.group(1)), int(m.group(2))
        except Exception:
            pass

    # Try hipconfig --version (outputs bare version like "6.3.21234.2")
    hipconfig = shutil.which("hipconfig")
    if hipconfig:
        try:
            result = subprocess.run(
                [hipconfig, "--version"],
                stdout = subprocess.PIPE,
                stderr = subprocess.DEVNULL,
                timeout = 5,
            )
            if result.returncode == 0:
                raw = result.stdout.decode().strip().split("\n")[0]
                parts = raw.split(".")
                if (
                    len(parts) >= 2
                    and parts[0].isdigit()
                    and parts[1].split("-")[0].isdigit()
                ):
                    return int(parts[0]), int(parts[1].split("-")[0])
        except Exception:
            pass

    # Distro package-manager fallbacks. Package-managed ROCm installs can
    # expose GPUs via rocminfo / amd-smi but still lack /opt/rocm/.info/version
    # and hipconfig, so probe dpkg (Debian/Ubuntu) and rpm (RHEL/Fedora/SUSE)
    # for the rocm-core package version. Matches the chain in
    # install.sh::get_torch_index_url so `unsloth studio update` behaves
    # the same as a fresh `curl | sh` install.
    import re as _re_pkg

    for cmd in (
        ["dpkg-query", "-W", "-f=${Version}\n", "rocm-core"],
        ["rpm", "-q", "--qf", "%{VERSION}\n", "rocm-core"],
    ):
        exe = shutil.which(cmd[0])
        if not exe:
            continue
        try:
            result = subprocess.run(
                [exe, *cmd[1:]],
                stdout = subprocess.PIPE,
                stderr = subprocess.DEVNULL,
                text = True,
                timeout = 5,
            )
        except Exception:
            continue
        if result.returncode != 0 or not result.stdout.strip():
            continue
        raw = result.stdout.strip()
        # dpkg can prepend an epoch ("1:6.3.0-1"); strip it before parsing.
        raw = _re_pkg.sub(r"^\d+:", "", raw)
        m = _re_pkg.match(r"(\d+)[.-](\d+)", raw)
        if m:
            return int(m.group(1)), int(m.group(2))

    return None