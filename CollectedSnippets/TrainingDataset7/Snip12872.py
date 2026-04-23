def split_domain_port(host):
    """
    Return a (domain, port) tuple from a given host.

    Returned domain is lowercased. If the host is invalid, the domain will be
    empty.
    """
    if match := host_validation_re.fullmatch(host.lower()):
        domain, port = match.groups(default="")
        # Remove a trailing dot (if present) from the domain.
        return domain.removesuffix("."), port
    return "", ""