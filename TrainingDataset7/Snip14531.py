def parse_etags(etag_str):
    """
    Parse a string of ETags given in an If-None-Match or If-Match header as
    defined by RFC 9110. Return a list of quoted ETags, or ['*'] if all ETags
    should be matched.
    """
    if etag_str.strip() == "*":
        return ["*"]
    else:
        # Parse each ETag individually, and return any that are valid.
        etag_matches = (ETAG_MATCH.match(etag.strip()) for etag in etag_str.split(","))
        return [match[1] for match in etag_matches if match]