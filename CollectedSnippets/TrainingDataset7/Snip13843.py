def skipUnlessAnyDBFeature(*features):
    """Skip a test unless a database has any of the named features."""
    return _deferredSkip(
        lambda: not any(getattr(connection.features, feature) for feature in features),
        "Database doesn't support any of the feature(s): %s" % ", ".join(features),
        "skipUnlessAnyDBFeature",
    )