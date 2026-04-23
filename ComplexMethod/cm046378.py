def check_apt_requirements(requirements):
    """Check if apt packages are installed and install missing ones.

    Args:
        requirements (list[str]): List of apt package names to check and install.
    """
    prefix = colorstr("red", "bold", "apt requirements:")
    # Check which packages are missing
    missing_packages = []
    for package in requirements:
        try:
            # Use dpkg -l to check if package is installed
            result = subprocess.run(["dpkg", "-l", package], capture_output=True, text=True, check=False)
            # Check if package is installed (look for "ii" status)
            if result.returncode != 0 or not any(
                line.startswith("ii") and package in line for line in result.stdout.splitlines()
            ):
                missing_packages.append(package)
        except Exception:
            # If check fails, assume package is not installed
            missing_packages.append(package)

    # Install missing packages if any
    if missing_packages:
        LOGGER.info(
            f"{prefix} Ultralytics requirement{'s' * (len(missing_packages) > 1)} {missing_packages} not found, attempting AutoUpdate..."
        )
        # Optionally update package list first
        cmd = (["sudo"] if is_sudo_available() else []) + ["apt", "update"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Build and run the install command
        cmd = (["sudo"] if is_sudo_available() else []) + ["apt", "install", "-y"] + missing_packages
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        LOGGER.info(f"{prefix} AutoUpdate success ✅")
        LOGGER.warning(f"{prefix} {colorstr('bold', 'Restart runtime or rerun command for updates to take effect')}\n")