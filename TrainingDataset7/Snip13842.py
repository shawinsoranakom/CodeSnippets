def skipUnlessDBFeature(*features):
    """Skip a test unless a database has all the named features."""
    return _deferredSkip(
        lambda: not all(getattr(connection.features, feature) for feature in features),
        "Database doesn't support feature(s): %s" % ", ".join(features),
        "skipUnlessDBFeature",
    )