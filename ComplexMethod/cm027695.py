def validate_requirements_format(integration: Integration) -> bool:
    """Validate requirements format.

    Returns if valid.
    """
    start_errors = len(integration.errors)

    for req in integration.requirements:
        if " " in req:
            integration.add_error(
                "requirements",
                f'Requirement "{req}" contains a space',
            )
            continue

        if not (match := PACKAGE_REGEX.match(req)):
            integration.add_error(
                "requirements",
                f'Requirement "{req}" does not match package regex pattern',
            )
            continue
        pkg, sep, version = match.groups()

        if integration.core and sep != "==":
            integration.add_error(
                "requirements",
                f'Requirement {req} need to be pinned "<pkg name>==<version>".',
            )
            continue

        if not version:
            continue

        if integration.core:
            for part in version.split(";", 1)[0].split(","):
                version_part = PIP_VERSION_RANGE_SEPARATOR.match(part)
                if (
                    version_part
                    and AwesomeVersion(version_part.group(2)).strategy
                    == AwesomeVersionStrategy.UNKNOWN
                ):
                    integration.add_error(
                        "requirements",
                        f"Unable to parse package version ({version}) for {pkg}.",
                    )
                    continue

    return len(integration.errors) == start_errors