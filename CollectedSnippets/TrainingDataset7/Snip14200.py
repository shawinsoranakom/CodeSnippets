def patch_vary_headers(response, newheaders):
    """
    Add (or update) the "Vary" header in the given HttpResponse object.
    newheaders is a list of header names that should be in "Vary". If headers
    contains an asterisk, then "Vary" header will consist of a single asterisk
    '*'. Otherwise, existing headers in "Vary" aren't removed.
    """
    # Note that we need to keep the original order intact, because cache
    # implementations may rely on the order of the Vary contents in, say,
    # computing an MD5 hash.
    if response.has_header("Vary"):
        vary_headers = cc_delim_re.split(response.headers["Vary"])
    else:
        vary_headers = []
    # Use .lower() here so we treat headers as case-insensitive.
    existing_headers = {header.lower() for header in vary_headers}
    additional_headers = [
        newheader
        for newheader in newheaders
        if newheader.lower() not in existing_headers
    ]
    vary_headers += additional_headers
    if "*" in vary_headers:
        response.headers["Vary"] = "*"
    else:
        response.headers["Vary"] = ", ".join(vary_headers)