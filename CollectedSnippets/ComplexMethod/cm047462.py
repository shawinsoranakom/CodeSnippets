def adapt_version(version: str) -> str:
    """Reformat the version of the module into a canonical format."""
    version_str_parts = version.split('.')
    if not (2 <= len(version_str_parts) <= 5):
        raise ValueError(f"Invalid version {version!r}, must have between 2 and 5 parts")
    serie = release.major_version
    if version.startswith(serie) and not version_str_parts[0].isdigit():
        # keep only digits for parsing
        version_str_parts[0] = ''.join(c for c in version_str_parts[0] if c.isdigit())
    try:
        version_parts = [int(v) for v in version_str_parts]
    except ValueError as e:
        raise ValueError(f"Invalid version {version!r}") from e
    if len(version_parts) <= 3 and not version.startswith(serie):
        # prefix the version with serie
        return f"{serie}.{version}"
    return version