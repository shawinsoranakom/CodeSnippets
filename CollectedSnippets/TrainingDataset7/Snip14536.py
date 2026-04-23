def escape_leading_slashes(url):
    """
    If redirecting to an absolute path (two leading slashes), a slash must be
    escaped to prevent browsers from handling the path as schemaless and
    redirecting to another host.
    """
    if url.startswith("//"):
        url = "/%2F{}".format(url.removeprefix("//"))
    return url