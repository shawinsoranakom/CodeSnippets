def load(unicode_version: str = "auto") -> CellTable:
    """Load a cell table for the given unicode version.

    Args:
        unicode_version: Unicode version, or `None` to auto-detect.

    """
    if unicode_version == "auto":
        unicode_version = os.environ.get("UNICODE_VERSION", "latest")
        try:
            _parse_version(unicode_version)
        except ValueError:
            # The environment variable is invalid
            # Fallback to using the latest version seems reasonable
            unicode_version = "latest"

    if unicode_version == "latest":
        version = VERSIONS[-1]
    else:
        try:
            version_numbers = _parse_version(unicode_version)
        except ValueError:
            version_numbers = _parse_version(VERSIONS[-1])
        major, minor, patch = version_numbers
        version = f"{major}.{minor}.{patch}"
        if version not in VERSION_SET:
            insert_position = bisect.bisect_left(VERSION_ORDER, version_numbers)
            version = VERSIONS[max(0, insert_position - 1)]

    version_path_component = version.replace(".", "-")
    module_name = f".unicode{version_path_component}"
    module = import_module(module_name, "rich._unicode_data")
    if TYPE_CHECKING:
        assert isinstance(module.cell_table, CellTable)
    return module.cell_table