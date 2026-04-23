def get_requirements(integration: Integration, packages: set[str]) -> set[str]:
    """Return all (recursively) requirements for an integration."""
    deptree = get_pipdeptree()

    all_requirements = set()

    to_check = deque(packages)

    forbidden_package_exceptions = FORBIDDEN_PACKAGE_EXCEPTIONS.get(
        integration.domain, {}
    )
    needs_forbidden_package_exceptions = False

    packages_checked_files: set[str] = set()
    forbidden_package_files_exceptions = FORBIDDEN_PACKAGE_FILES_EXCEPTIONS.get(
        integration.domain, {}
    )
    needs_forbidden_package_files_exception = False

    package_version_check_exceptions = PACKAGE_CHECK_VERSION_RANGE_EXCEPTIONS.get(
        integration.domain, {}
    )
    needs_package_version_check_exception = False

    python_version_check_exceptions = PYTHON_VERSION_CHECK_EXCEPTIONS.get(
        integration.domain, {}
    )
    needs_python_version_check_exception = False

    while to_check:
        package = to_check.popleft()

        if package in all_requirements:
            continue

        all_requirements.add(package)

        item = deptree.get(package)

        if item is None:
            # Only warn if direct dependencies could not be resolved
            if package in packages:
                integration.add_error(
                    "requirements", f"Failed to resolve requirements for {package}"
                )
            continue

        # Check for restrictive version limits on Python
        if (requires_python := metadata_cache(package)["Requires-Python"]) and not all(
            _is_dependency_version_range_valid(version_part, "SemVer")
            for version_part in requires_python.split(",")
        ):
            needs_python_version_check_exception = True
            integration.add_warning_or_error(
                package in python_version_check_exceptions.get("homeassistant", set()),
                "requirements",
                "Version restrictions for Python are too strict "
                f"({requires_python}) in {package}",
            )

        # Check package names
        if package not in packages_checked_files:
            packages_checked_files.add(package)
            if not check_dependency_files(
                integration,
                "homeassistant",
                package,
                forbidden_package_files_exceptions.get("homeassistant", ()),
            ):
                needs_forbidden_package_files_exception = True

        # Use inner loop to check dependencies
        # so we have access to the dependency parent (=current package)
        dependencies: dict[str, str] = item["dependencies"]
        for pkg, version in dependencies.items():
            # Check for forbidden packages
            if pkg.startswith("types-") or pkg in FORBIDDEN_PACKAGES:
                reason = FORBIDDEN_PACKAGES.get(pkg, "not be a runtime dependency")
                needs_forbidden_package_exceptions = True
                integration.add_warning_or_error(
                    pkg in forbidden_package_exceptions.get(package, set()),
                    "requirements",
                    f"Package {pkg} should {reason} in {package}",
                )
            # Check for restrictive version limits on common packages
            if not check_dependency_version_range(
                integration,
                package,
                pkg,
                version,
                package_version_check_exceptions.get(package, set()),
            ):
                needs_package_version_check_exception = True

            # Check package names
            if pkg not in packages_checked_files:
                packages_checked_files.add(pkg)
                if not check_dependency_files(
                    integration,
                    package,
                    pkg,
                    forbidden_package_files_exceptions.get(package, ()),
                ):
                    needs_forbidden_package_files_exception = True

        to_check.extend(dependencies)

    if forbidden_package_exceptions and not needs_forbidden_package_exceptions:
        integration.add_error(
            "requirements",
            f"Integration {integration.domain} runtime dependency exceptions "
            "have been resolved, please remove from `FORBIDDEN_PACKAGE_EXCEPTIONS`",
        )
    if package_version_check_exceptions and not needs_package_version_check_exception:
        integration.add_error(
            "requirements",
            f"Integration {integration.domain} version restrictions checks have been "
            "resolved, please remove from `PACKAGE_CHECK_VERSION_RANGE_EXCEPTIONS`",
        )
    if python_version_check_exceptions and not needs_python_version_check_exception:
        integration.add_error(
            "requirements",
            f"Integration {integration.domain} version restrictions for Python have "
            "been resolved, please remove from `PYTHON_VERSION_CHECK_EXCEPTIONS`",
        )
    if (
        forbidden_package_files_exceptions
        and not needs_forbidden_package_files_exception
    ):
        integration.add_error(
            "requirements",
            f"Integration {integration.domain} runtime files dependency exceptions "
            "have been resolved, please remove from `FORBIDDEN_PACKAGE_FILES_EXCEPTIONS`",
        )

    return all_requirements