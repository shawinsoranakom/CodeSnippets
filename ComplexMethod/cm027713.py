def _check_requirements_are_typed(integration: Integration) -> list[str]:
    """Check if all requirements are typed."""
    invalid_requirements = []
    for requirement in integration.requirements:
        requirement_name, requirement_version = requirement.split("==")
        # Remove any extras
        requirement_name = requirement_name.split("[")[0]
        try:
            distribution = metadata.distribution(requirement_name)
        except metadata.PackageNotFoundError:
            # Package not installed locally
            continue
        if distribution.version != requirement_version:
            # Version out of date locally
            continue

        if not any(file for file in distribution.files if file.name == "py.typed"):
            # no py.typed file
            try:
                metadata.distribution(f"types-{requirement_name}")
            except metadata.PackageNotFoundError:
                # also no stubs-only package
                invalid_requirements.append(requirement)

    return invalid_requirements