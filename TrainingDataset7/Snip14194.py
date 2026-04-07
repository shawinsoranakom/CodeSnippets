def _if_match_passes(target_etag, etags):
    """
    Test the If-Match comparison as defined in RFC 9110 Section 13.1.1.
    """
    if not target_etag:
        # If there isn't an ETag, then there can't be a match.
        return False
    elif etags == ["*"]:
        # The existence of an ETag means that there is "a current
        # representation for the target resource", even if the ETag is weak,
        # so there is a match to '*'.
        return True
    elif target_etag.startswith("W/"):
        # A weak ETag can never strongly match another ETag.
        return False
    else:
        # Since the ETag is strong, this will only return True if there's a
        # strong match.
        return target_etag in etags