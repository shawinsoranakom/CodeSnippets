def _if_none_match_passes(target_etag, etags):
    """
    Test the If-None-Match comparison as defined in RFC 9110 Section 13.1.2.
    """
    if not target_etag:
        # If there isn't an ETag, then there isn't a match.
        return True
    elif etags == ["*"]:
        # The existence of an ETag means that there is "a current
        # representation for the target resource", so there is a match to '*'.
        return False
    else:
        # The comparison should be weak, so look for a match after stripping
        # off any weak indicators.
        target_etag = target_etag.strip("W/")
        etags = (etag.strip("W/") for etag in etags)
        return target_etag not in etags