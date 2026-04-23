def _is_dependency_version_range_valid(
    version_part: str, convention: str, pkg: str | None = None
) -> bool:
    prepare_update = PACKAGE_CHECK_PREPARE_UPDATE.get(pkg) if pkg else None
    version_match = PIP_VERSION_RANGE_SEPARATOR.match(version_part.strip())
    operator = version_match.group(1)
    version = version_match.group(2)
    awesome = AwesomeVersion(version)

    if operator in (">", ">=", "!="):
        # Lower version binding and version exclusion are fine
        return True

    if prepare_update is not None:
        if operator in ("==", "~="):
            # Only current major version allowed which prevents updates to the next one
            return False
        # Allow upper constraints for major version + 1
        if operator == "<" and awesome.section(0) < prepare_update + 1:
            return False
        if operator == "<=" and awesome.section(0) < prepare_update:
            return False

    if convention == "SemVer":
        if operator == "==":
            # Explicit version with wildcard is allowed only on major version
            # e.g. ==1.* is allowed, but ==1.2.* is not
            return version.endswith(".*") and version.count(".") == 1

        if operator in ("<", "<="):
            # Upper version binding only allowed on major version
            # e.g. <=3 is allowed, but <=3.1 is not
            return awesome.section(1) == 0 and awesome.section(2) == 0

        if operator == "~=":
            # Compatible release operator is only allowed on major or minor version
            # e.g. ~=1.2 is allowed, but ~=1.2.3 is not
            return awesome.section(2) == 0

    return False