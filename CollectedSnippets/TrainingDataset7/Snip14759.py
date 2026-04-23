def get_complete_version(version=None):
    """
    Return a tuple of the django version. If version argument is non-empty,
    check for correctness of the tuple provided.
    """
    if version is None:
        from django import VERSION as version
    else:
        assert len(version) == 5
        assert version[3] in ("alpha", "beta", "rc", "final")

    return version