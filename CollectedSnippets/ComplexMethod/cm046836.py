def check_package_installed(package_name, package_manager = None):
    """Check if a package is installed using the system package manager"""

    if package_manager is None:
        package_manager = detect_package_manager()

    if package_manager is None:
        print("Warning: Could not detect package manager")
        return None

    try:
        if package_manager == "apt":
            # Check with dpkg
            result = subprocess.run(
                ["dpkg", "-l", package_name], capture_output = True, text = True
            )
            return result.returncode == 0

        elif package_manager in ["yum", "dnf"]:
            # Check with rpm
            result = subprocess.run(
                ["rpm", "-q", package_name], capture_output = True, text = True
            )
            return result.returncode == 0

        elif package_manager == "pacman":
            result = subprocess.run(
                ["pacman", "-Q", package_name], capture_output = True, text = True
            )
            return result.returncode == 0

        elif package_manager == "zypper":
            result = subprocess.run(
                ["zypper", "se", "-i", package_name], capture_output = True, text = True
            )
            return package_name in result.stdout

    except Exception as e:
        print(f"Error checking package: {e}")
        return None