def create_server(address, *, family=AF_INET, backlog=None, reuse_port=False,
                  dualstack_ipv6=False):
    """Convenience function which creates a SOCK_STREAM type socket
    bound to *address* (a 2-tuple (host, port)) and return the socket
    object.

    *family* should be either AF_INET or AF_INET6.
    *backlog* is the queue size passed to socket.listen().
    *reuse_port* dictates whether to use the SO_REUSEPORT socket option.
    *dualstack_ipv6*: if true and the platform supports it, it will
    create an AF_INET6 socket able to accept both IPv4 or IPv6
    connections. When false it will explicitly disable this option on
    platforms that enable it by default (e.g. Linux).

    >>> with create_server(('', 8000)) as server:
    ...     while True:
    ...         conn, addr = server.accept()
    ...         # handle new connection
    """
    if reuse_port and not hasattr(_socket, "SO_REUSEPORT"):
        raise ValueError("SO_REUSEPORT not supported on this platform")
    if dualstack_ipv6:
        if not has_dualstack_ipv6():
            raise ValueError("dualstack_ipv6 not supported on this platform")
        if family != AF_INET6:
            raise ValueError("dualstack_ipv6 requires AF_INET6 family")
    sock = socket(family, SOCK_STREAM)
    try:
        # Note about Windows. We don't set SO_REUSEADDR because:
        # 1) It's unnecessary: bind() will succeed even in case of a
        # previous closed socket on the same address and still in
        # TIME_WAIT state.
        # 2) If set, another socket is free to bind() on the same
        # address, effectively preventing this one from accepting
        # connections. Also, it may set the process in a state where
        # it'll no longer respond to any signals or graceful kills.
        # See: https://learn.microsoft.com/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse
        if os.name not in ('nt', 'cygwin') and \
                hasattr(_socket, 'SO_REUSEADDR'):
            try:
                sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            except error:
                # Fail later on bind(), for platforms which may not
                # support this option.
                pass
        # Since Linux 6.12.9, SO_REUSEPORT is not allowed
        # on other address families than AF_INET/AF_INET6.
        if reuse_port and family in (AF_INET, AF_INET6):
            sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        if has_ipv6 and family == AF_INET6:
            if dualstack_ipv6:
                sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 0)
            elif hasattr(_socket, "IPV6_V6ONLY") and \
                    hasattr(_socket, "IPPROTO_IPV6"):
                sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 1)
        try:
            sock.bind(address)
        except error as err:
            msg = '%s (while attempting to bind on address %r)' % \
                (err.strerror, address)
            raise error(err.errno, msg) from None
        if backlog is None:
            sock.listen()
        else:
            sock.listen(backlog)
        return sock
    except error:
        sock.close()
        raise