def default_trim_value():
    """
    GEOS changed the default value in 3.12.0. Can be replaced by True when
    3.12.0 becomes the minimum supported version.
    """
    return geos_version_tuple() >= (3, 12)