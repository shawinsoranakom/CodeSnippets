def static(path):
    """
    Given a relative path to a static asset, return the absolute path to the
    asset.
    """
    return StaticNode.handle_simple(path)