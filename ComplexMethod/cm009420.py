def _get_sub_deps(packages: Sequence[str]) -> list[str]:
    """Get any specified sub-dependencies."""
    sub_deps = set()
    underscored_packages = {pkg.replace("-", "_") for pkg in packages}

    for pkg in packages:
        try:
            required = metadata.requires(pkg)
        except metadata.PackageNotFoundError:
            continue

        if not required:
            continue

        for req in required:
            # Extract package name (e.g., "httpx<1,>=0.23.0" -> "httpx")
            match = re.match(r"^([a-zA-Z0-9_.-]+)", req)
            if match:
                pkg_name = match.group(1)
                if pkg_name.replace("-", "_") not in underscored_packages:
                    sub_deps.add(pkg_name)

    return sorted(sub_deps, key=lambda x: x.lower())