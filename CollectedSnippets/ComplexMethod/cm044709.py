def detect() -> OSInfo:
    """
    Fully detect the current OS, distro, and available package manager.
    Never asks the user — entirely automatic.
    """
    import os

    system_raw = platform.system()
    system = system_raw.lower()
    if system == "darwin":
        system = "macos"

    info = OSInfo(
        system  = system,
        is_root = (os.geteuid() == 0) if hasattr(os, "geteuid") else False,
        home_dir = Path.home(),
        arch    = platform.machine(),
    )

    # ── Linux-specific ─────────────────────────────────────────────────────────
    if system == "linux":
        # Detect WSL
        try:
            info.is_wsl = "microsoft" in Path("/proc/version").read_text().lower()
        except (FileNotFoundError, PermissionError):
            pass

        # Read /etc/os-release (standard on all modern distros)
        os_release: dict[str, str] = {}
        for path in ("/etc/os-release", "/usr/lib/os-release"):
            try:
                for line in Path(path).read_text().splitlines():
                    k, _, v = line.partition("=")
                    os_release[k.strip()] = v.strip().strip('"')
                break
            except FileNotFoundError:
                continue

        info.distro_id      = os_release.get("ID", "").lower()
        info.distro_like    = os_release.get("ID_LIKE", "").lower()
        info.distro_version = os_release.get("VERSION_ID", "")

    # ── Package manager detection (in priority order) ──────────────────────────
    for mgr in ("apt-get", "pacman", "dnf", "zypper", "apk", "brew", "pkg"):
        if shutil.which(mgr):
            info.pkg_manager = mgr
            break

    return info