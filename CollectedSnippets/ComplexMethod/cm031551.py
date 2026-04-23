def proxy_bypass_environment(host, proxies=None):
    """Test if proxies should not be used for a particular host.

    Checks the proxy dict for the value of no_proxy, which should
    be a list of comma separated DNS suffixes, or '*' for all hosts.

    """
    if proxies is None:
        proxies = getproxies_environment()
    # don't bypass, if no_proxy isn't specified
    try:
        no_proxy = proxies['no']
    except KeyError:
        return False
    # '*' is special case for always bypass
    if no_proxy == '*':
        return True
    host = host.lower()
    # strip port off host
    hostonly, port = _splitport(host)
    # check if the host ends with any of the DNS suffixes
    for name in no_proxy.split(','):
        name = name.strip()
        if name:
            name = name.lstrip('.')  # ignore leading dots
            name = name.lower()
            if hostonly == name or host == name:
                return True
            name = '.' + name
            if hostonly.endswith(name) or host.endswith(name):
                return True
    # otherwise, don't bypass
    return False