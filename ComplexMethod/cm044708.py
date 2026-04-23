def check_os_compatibility():
    """Print detected OS info and exit on unsupported systems."""
    info = CURRENT_OS
    console.print(
        f"[dim]Detected: OS={info.system} | distro={info.distro_id or 'n/a'} | "
        f"pkg_mgr={info.pkg_manager or 'none'} | arch={info.arch}[/dim]"
    )

    if info.system == "windows":
        console.print(Panel(
            "[error]Windows is not supported natively.[/error]\n"
            "Use WSL2 with a Kali or Ubuntu image.",
            border_style="red",
        ))
        sys.exit(1)

    if info.is_wsl:
        console.print("[warning]WSL detected. Wireless tools will NOT work in WSL.[/warning]")

    if info.system == "macos":
        console.print(Panel(
            "[warning]macOS support is partial.[/warning]\n"
            "Network/wireless tools require Linux. OSINT and web tools work.",
            border_style="yellow",
        ))
        if not shutil.which("brew"):
            console.print("[error]Homebrew not found. Install it first: https://brew.sh[/error]")
            sys.exit(1)

    if not info.pkg_manager:
        console.print("[warning]No supported package manager found.[/warning]")
        console.print("[dim]Supported: apt-get, pacman, dnf, zypper, apk, brew[/dim]")