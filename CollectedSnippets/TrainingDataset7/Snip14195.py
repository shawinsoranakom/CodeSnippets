def _if_unmodified_since_passes(last_modified, if_unmodified_since):
    """
    Test the If-Unmodified-Since comparison as defined in RFC 9110 Section
    13.1.4.
    """
    return last_modified and last_modified <= if_unmodified_since