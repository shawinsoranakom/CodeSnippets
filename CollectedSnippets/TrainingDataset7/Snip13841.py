def skipIfDBFeature(*features):
    """Skip a test if a database has at least one of the named features."""
    return _deferredSkip(
        lambda: any(getattr(connection.features, feature) for feature in features),
        "Database has feature(s) %s" % ", ".join(features),
        "skipIfDBFeature",
    )