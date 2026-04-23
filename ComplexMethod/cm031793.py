def verify_wheel(package_name: str) -> bool:
    # Find the package on disk
    package_paths = list(WHEEL_DIR.glob(f"{package_name}*.whl"))
    if len(package_paths) != 1:
        if package_paths:
            for p in package_paths:
                print_error(p, f"Found more than one wheel for package {package_name}.")
        else:
            print_error("", f"Could not find a {package_name} wheel on disk.")
        return False

    package_path = package_paths[0]

    print(f"Verifying checksum for {package_path}.")

    # Find the version of the package used by ensurepip
    package_version_match = re.search(
        f'_{package_name.upper()}_VERSION = "([^"]+)', ENSURE_PIP_INIT_PY_TEXT
    )
    if not package_version_match:
        print_error(
            package_path,
            f"No {package_name} version found in Lib/ensurepip/__init__.py.",
        )
        return False
    package_version = package_version_match[1]

    # Get the SHA 256 digest from the Cheeseshop
    try:
        raw_text = urlopen(f"https://pypi.org/pypi/{package_name}/json").read()
    except (OSError, ValueError):
        print_error(package_path, f"Could not fetch JSON metadata for {package_name}.")
        return False

    release_files = json.loads(raw_text)["releases"][package_version]
    expected_digest = ""
    for release_info in release_files:
        if package_path.name != release_info["filename"]:
            continue
        expected_digest = release_info["digests"].get("sha256", "")
        break
    else:
        print_error(package_path, f"No digest for {package_name} found from PyPI.")
        return False

    # Compute the SHA 256 digest of the wheel on disk
    actual_digest = hashlib.sha256(package_path.read_bytes()).hexdigest()

    print(f"Expected digest: {expected_digest}")
    print(f"Actual digest:   {actual_digest}")

    if actual_digest != expected_digest:
        print_error(
            package_path, f"Failed to verify the checksum of the {package_name} wheel."
        )
        return False

    print_notice(
        package_path,
        f"Successfully verified the checksum of the {package_name} wheel.",
    )
    return True