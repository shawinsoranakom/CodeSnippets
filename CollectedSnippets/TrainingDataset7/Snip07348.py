def geos_version_tuple():
    """Return the GEOS version as a tuple (major, minor, subminor)."""
    return get_version_tuple(geos_version().decode())