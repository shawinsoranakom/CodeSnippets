def has_vary_header(response, header_query):
    """
    Check to see if the response has a given header name in its Vary header.
    """
    if not response.has_header("Vary"):
        return False
    vary_headers = cc_delim_re.split(response.headers["Vary"])
    existing_headers = {header.lower() for header in vary_headers}
    return header_query.lower() in existing_headers