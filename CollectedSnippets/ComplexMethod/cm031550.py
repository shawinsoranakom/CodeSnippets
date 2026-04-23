def getproxies_environment():
    """Return a dictionary of scheme -> proxy server URL mappings.

    Scan the environment for variables named <scheme>_proxy;
    this seems to be the standard convention.
    """
    # in order to prefer lowercase variables, process environment in
    # two passes: first matches any, second pass matches lowercase only

    # select only environment variables which end in (after making lowercase) _proxy
    proxies = {}
    environment = []
    for name in os.environ:
        # fast screen underscore position before more expensive case-folding
        if len(name) > 5 and name[-6] == "_" and name[-5:].lower() == "proxy":
            value = os.environ[name]
            proxy_name = name[:-6].lower()
            environment.append((name, value, proxy_name))
            if value:
                proxies[proxy_name] = value
    # CVE-2016-1000110 - If we are running as CGI script, forget HTTP_PROXY
    # (non-all-lowercase) as it may be set from the web server by a "Proxy:"
    # header from the client
    # If "proxy" is lowercase, it will still be used thanks to the next block
    if 'REQUEST_METHOD' in os.environ:
        proxies.pop('http', None)
    for name, value, proxy_name in environment:
        # not case-folded, checking here for lower-case env vars only
        if name[-6:] == '_proxy':
            if value:
                proxies[proxy_name] = value
            else:
                proxies.pop(proxy_name, None)
    return proxies