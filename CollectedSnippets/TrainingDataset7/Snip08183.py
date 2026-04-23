def add_domain(domain, url, secure=False):
    protocol = "https" if secure else "http"
    if url.startswith("//"):
        # Support network-path reference (see #16753) - RSS requires a protocol
        url = "%s:%s" % (protocol, url)
    elif not url.startswith(("http://", "https://", "mailto:")):
        url = iri_to_uri("%s://%s%s" % (protocol, domain, url))
    return url