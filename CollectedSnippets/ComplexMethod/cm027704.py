def find_non_referenced_integrations(
    integrations: dict[str, Integration],
    integration: Integration,
    references: dict[Path, set[str]],
) -> set[str]:
    """Find integrations that are not allowed to be referenced."""
    allowed_references = calc_allowed_references(integration)
    referenced = set()
    for path, refs in references.items():
        if len(path.parts) == 1:
            # climate.py is stored as climate
            cur_fil_dir = path.stem
        else:
            # climate/__init__.py is stored as climate
            cur_fil_dir = path.parts[0]

        is_platform_other_integration = cur_fil_dir in integrations

        for ref in refs:
            # We are always allowed to import from ourselves
            if ref == integration.domain:
                continue

            # These references are approved based on the manifest
            if ref in allowed_references:
                continue

            # Some violations are whitelisted
            if (integration.domain, ref) in IGNORE_VIOLATIONS:
                continue

            # If it's a platform for another integration, the other integration is ok
            if is_platform_other_integration and cur_fil_dir == ref:
                continue

            # These have a platform specified in this integration
            if not is_platform_other_integration and (
                (integration.path / f"{ref}.py").is_file()
                # Platform dir
                or (integration.path / ref).is_dir()
            ):
                continue

            referenced.add(ref)

    return referenced