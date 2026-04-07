def _if_modified_since_passes(last_modified, if_modified_since):
    """
    Test the If-Modified-Since comparison as defined in RFC 9110 Section
    13.1.3.
    """
    return not last_modified or last_modified > if_modified_since