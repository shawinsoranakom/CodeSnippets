def create_connection(
    address,
    timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
    source_address=None,
    *,
    _create_socket_func=_socket_connect,
):
    # Work around socket.create_connection() which tries all addresses from getaddrinfo() including IPv6.
    # This filters the addresses based on the given source_address.
    # Based on: https://github.com/python/cpython/blob/main/Lib/socket.py#L810
    host, port = address
    ip_addrs = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    if not ip_addrs:
        raise OSError('getaddrinfo returns an empty list')
    if source_address is not None:
        af = socket.AF_INET if ':' not in source_address[0] else socket.AF_INET6
        ip_addrs = [addr for addr in ip_addrs if addr[0] == af]
        if not ip_addrs:
            raise OSError(
                f'No remote IPv{4 if af == socket.AF_INET else 6} addresses available for connect. '
                f'Can\'t use "{source_address[0]}" as source address')

    err = None
    for ip_addr in ip_addrs:
        try:
            sock = _create_socket_func(ip_addr, timeout, source_address)
            # Explicitly break __traceback__ reference cycle
            # https://bugs.python.org/issue36820
            err = None
            return sock
        except OSError as e:
            err = e

    try:
        raise err
    finally:
        # Explicitly break __traceback__ reference cycle
        # https://bugs.python.org/issue36820
        err = None