def check_dependency_files(
    integration: Integration,
    package: str,
    pkg: str,
    package_exceptions: Collection[str],
) -> bool:
    """Check dependency files for forbidden files and forbidden package names."""
    if (results := _packages_checked_files_cache.get(pkg)) is None:
        top_level: set[str] = set()
        file_names: set[str] = set()
        for file in files(pkg) or ():
            if not (top := file.parts[0].lower()).endswith((".dist-info", ".py")):
                top_level.add(top)
            if (name := str(file).lower()) in FORBIDDEN_FILE_NAMES or (
                name.endswith(".pth") and len(file.parts) == 1
            ):
                file_names.add(str(file))
        results = _PackageFilesCheckResult(
            top_level=FORBIDDEN_PACKAGE_NAMES & top_level,
            file_names=file_names,
        )
        _packages_checked_files_cache[pkg] = results
    if not (results["top_level"] or results["file_names"]):
        return True

    for dir_name in results["top_level"]:
        integration.add_warning_or_error(
            pkg in package_exceptions,
            "requirements",
            f"Package {pkg} has a forbidden top level directory '{dir_name}' in {package}",
        )
    for file_name in results["file_names"]:
        integration.add_warning_or_error(
            pkg in package_exceptions,
            "requirements",
            f"Package {pkg} has a forbidden file '{file_name}' in {package}",
        )
    return False