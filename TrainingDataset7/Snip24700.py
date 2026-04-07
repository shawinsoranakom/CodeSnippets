def skipUnlessGISLookup(*gis_lookups):
    """
    Skip a test unless a database supports all of gis_lookups.
    """

    def decorator(test_func):
        @wraps(test_func)
        def skip_wrapper(*args, **kwargs):
            if any(key not in connection.ops.gis_operators for key in gis_lookups):
                raise unittest.SkipTest(
                    "Database doesn't support all the lookups: %s"
                    % ", ".join(gis_lookups)
                )
            return test_func(*args, **kwargs)

        return skip_wrapper

    return decorator