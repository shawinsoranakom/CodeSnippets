def validate_requirements(integration: Integration) -> None:
    """Validate requirements."""
    if not validate_requirements_format(integration):
        return

    integration_requirements = set()
    integration_packages = set()
    for req in integration.requirements:
        package = normalize_package_name(req)
        if not package:
            integration.add_error(
                "requirements",
                f"Failed to normalize package name from requirement {req}",
            )
            return
        if package in EXCLUDED_REQUIREMENTS_ALL:
            continue
        integration_requirements.add(req)
        integration_packages.add(package)

    if integration.disabled:
        return

    install_ok = install_requirements(integration, integration_requirements)

    if not install_ok:
        return

    all_integration_requirements = get_requirements(integration, integration_packages)

    if integration_requirements and not all_integration_requirements:
        integration.add_error(
            "requirements",
            f"Failed to resolve requirements {integration_requirements}",
        )
        return

    # Check for requirements incompatible with standard library.
    standard_library_violations = set()
    for req in all_integration_requirements:
        if req in sys.stdlib_module_names:
            standard_library_violations.add(req)

    if standard_library_violations:
        integration.add_error(
            "requirements",
            (
                f"Package {req} has dependencies {standard_library_violations} which "
                "are not compatible with the Python standard library"
            ),
        )